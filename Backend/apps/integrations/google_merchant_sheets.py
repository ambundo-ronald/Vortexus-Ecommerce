import json
import os
from typing import Any

from django.conf import settings

from .google_merchant_feed import GOOGLE_MERCHANT_FEED_HEADERS, build_google_merchant_feed_rows


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
) -> dict[str, Any]:
    spreadsheet_id = spreadsheet_id or getattr(settings, 'GOOGLE_MERCHANT_SHEETS_SPREADSHEET_ID', '')
    range_name = range_name or getattr(settings, 'GOOGLE_MERCHANT_SHEETS_RANGE', 'Sheet1!A1:AN')
    clear_range = clear_range or getattr(settings, 'GOOGLE_MERCHANT_SHEETS_CLEAR_RANGE', 'Sheet1!A:AN')
    if not spreadsheet_id:
        raise GoogleMerchantSheetsError('GOOGLE_MERCHANT_SHEETS_SPREADSHEET_ID is required.')

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
    return {
        'spreadsheet_id': spreadsheet_id,
        'range': range_name,
        'rows_written': len(values),
        'products_written': max(0, len(values) - 1),
        'updated_cells': result.get('updatedCells', 0),
        'updated_range': result.get('updatedRange', ''),
    }


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
