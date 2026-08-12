import json
import os
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.auditlog.services import sanitize_metadata

from .google_merchant_feed import GOOGLE_MERCHANT_FEED_HEADERS, build_google_merchant_feed_rows
from .models import IntegrationConnection, SyncEventLog, SyncJob


GOOGLE_SHEETS_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'


class GoogleMerchantSheetsError(Exception):
    pass


def google_merchant_sheet_values(*, tax_country_code: str = 'KE') -> list[list[str]]:
    rows = build_google_merchant_feed_rows(tax_country_code=tax_country_code)
    values = [GOOGLE_MERCHANT_FEED_HEADERS]
    for row in rows:
        values.append([str(row.get(header, '') or '') for header in GOOGLE_MERCHANT_FEED_HEADERS])
    return values


def sync_google_merchant_sheet(
    *,
    spreadsheet_id: str = '',
    range_name: str = '',
    clear_range: str = '',
    tax_country_code: str = 'KE',
    created_by=None,
) -> dict[str, Any]:
    spreadsheet_id = spreadsheet_id or getattr(settings, 'GOOGLE_MERCHANT_SHEETS_SPREADSHEET_ID', '')
    range_name = range_name or getattr(settings, 'GOOGLE_MERCHANT_SHEETS_RANGE', 'Sheet1!A1:AN')
    clear_range = clear_range or getattr(settings, 'GOOGLE_MERCHANT_SHEETS_CLEAR_RANGE', 'Sheet1!A:AN')
    if not spreadsheet_id:
        raise GoogleMerchantSheetsError('GOOGLE_MERCHANT_SHEETS_SPREADSHEET_ID is required.')

    connection = _google_merchant_connection()
    job = _start_sheet_sync_job(connection, created_by=created_by)
    try:
        service = _sheets_service()
        values = google_merchant_sheet_values(tax_country_code=tax_country_code)
        if clear_range:
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=clear_range,
                body={},
            ).execute()

        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body={'values': values},
        ).execute()
        summary = {
            'spreadsheet_id': spreadsheet_id,
            'range': range_name,
            'clear_range': clear_range,
            'rows_written': len(values),
            'products_written': max(0, len(values) - 1),
            'updated_cells': result.get('updatedCells', 0),
            'updated_range': result.get('updatedRange', ''),
        }
    except Exception as exc:
        _finish_sheet_sync_job(
            connection,
            job,
            status=SyncJob.STATUS_FAILED,
            spreadsheet_id=spreadsheet_id,
            summary={'spreadsheet_id': spreadsheet_id, 'range': range_name, 'clear_range': clear_range},
            error_message=str(exc),
        )
        raise

    _finish_sheet_sync_job(
        connection,
        job,
        status=SyncJob.STATUS_SUCCEEDED,
        spreadsheet_id=spreadsheet_id,
        summary=summary,
    )
    return summary


def _google_merchant_connection() -> IntegrationConnection | None:
    active = (
        IntegrationConnection.objects.filter(
            connection_type=IntegrationConnection.TYPE_GOOGLE_MERCHANT,
            is_active=True,
            status=IntegrationConnection.STATUS_ACTIVE,
        )
        .order_by('id')
        .first()
    )
    if active:
        return active

    return (
        IntegrationConnection.objects.filter(
            connection_type=IntegrationConnection.TYPE_GOOGLE_MERCHANT,
            is_active=True,
        )
        .order_by('id')
        .first()
    )


def _start_sheet_sync_job(connection: IntegrationConnection | None, *, created_by=None) -> SyncJob | None:
    if connection is None:
        return None

    return SyncJob.objects.create(
        connection=connection,
        job_type=SyncJob.TYPE_GOOGLE_SHEETS_EXPORT,
        direction=SyncJob.DIRECTION_OUTBOUND,
        status=SyncJob.STATUS_RUNNING,
        created_by=created_by if getattr(created_by, 'is_authenticated', False) else None,
        started_at=timezone.now(),
    )


def _finish_sheet_sync_job(
    connection: IntegrationConnection | None,
    job: SyncJob | None,
    *,
    status: str,
    spreadsheet_id: str,
    summary: dict[str, Any],
    error_message: str = '',
) -> None:
    if connection is None or job is None:
        return

    now = timezone.now()
    job.status = status
    job.summary = sanitize_metadata(summary)
    job.error_message = error_message
    job.finished_at = now
    job.save(update_fields=['status', 'summary', 'error_message', 'finished_at'])

    metadata = connection.metadata or {}
    metadata['google_sheets_last_sync'] = job.summary
    connection.metadata = metadata
    if status == SyncJob.STATUS_SUCCEEDED:
        connection.status = IntegrationConnection.STATUS_ACTIVE
        connection.last_successful_sync_at = now
        connection.save(update_fields=['status', 'metadata', 'last_successful_sync_at', 'updated_at'])
        event_status = SyncEventLog.STATUS_PROCESSED
    else:
        connection.status = IntegrationConnection.STATUS_ERROR
        connection.last_failed_sync_at = now
        connection.save(update_fields=['status', 'metadata', 'last_failed_sync_at', 'updated_at'])
        event_status = SyncEventLog.STATUS_FAILED

    SyncEventLog.objects.create(
        connection=connection,
        job=job,
        direction=SyncJob.DIRECTION_OUTBOUND,
        entity_type='google_sheet',
        external_reference=spreadsheet_id,
        status=event_status,
        payload_excerpt=job.summary,
        error_message=error_message,
    )


def _sheets_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GoogleMerchantSheetsError('google-api-python-client and google-auth are required for Google Sheets sync.') from exc

    credentials = service_account.Credentials.from_service_account_info(
        _service_account_info(),
        scopes=[GOOGLE_SHEETS_SCOPE],
    )
    return build('sheets', 'v4', credentials=credentials, cache_discovery=False)


def _service_account_info() -> dict[str, Any]:
    raw_json = (
        os.environ.get('GOOGLE_MERCHANT_SHEETS_SERVICE_ACCOUNT_JSON')
        or os.environ.get('GOOGLE_MERCHANT_SERVICE_ACCOUNT_JSON')
        or ''
    )
    if raw_json:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise GoogleMerchantSheetsError('Google Sheets service account JSON is invalid.') from exc

    file_path = (
        os.environ.get('GOOGLE_MERCHANT_SHEETS_SERVICE_ACCOUNT_FILE')
        or os.environ.get('GOOGLE_MERCHANT_SERVICE_ACCOUNT_FILE')
        or ''
    )
    if file_path:
        try:
            with open(file_path, encoding='utf-8') as handle:
                return json.load(handle)
        except OSError as exc:
            raise GoogleMerchantSheetsError(f'Could not read Google Sheets service account file: {exc}') from exc
        except json.JSONDecodeError as exc:
            raise GoogleMerchantSheetsError('Google Sheets service account file is invalid JSON.') from exc

    raise GoogleMerchantSheetsError('Google Sheets service account JSON or file path is required.')
