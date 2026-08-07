import json
import os
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.auditlog.services import sanitize_metadata
from apps.common.catalog import product_brand
from apps.common.products import stockrecord_count, stockrecord_currency, stockrecord_price

from .models import GoogleMerchantProductSync, IntegrationConnection, SyncEventLog, SyncJob


class GoogleMerchantIntegrationError(Exception):
    pass


GOOGLE_MERCHANT_SCOPE = 'https://www.googleapis.com/auth/content'
DEFAULT_MERCHANT_API_BASE_URL = 'https://merchantapi.googleapis.com'


def active_google_merchant_connections():
    return [
        connection
        for connection in IntegrationConnection.objects.filter(
            connection_type=IntegrationConnection.TYPE_GOOGLE_MERCHANT,
            is_active=True,
            status=IntegrationConnection.STATUS_ACTIVE,
        )
        if (connection.metadata or {}).get('enabled', True)
    ]


def queue_google_merchant_product_sync(product_id: int) -> None:
    if not active_google_merchant_connections():
        return

    from .tasks import sync_product_to_google_merchant

    transaction.on_commit(lambda: sync_product_to_google_merchant.delay(product_id))


def queue_google_merchant_product_delete(product_id: int, offer_id: str = '') -> None:
    if not active_google_merchant_connections():
        return

    from .tasks import delete_product_from_google_merchant

    transaction.on_commit(lambda: delete_product_from_google_merchant.delay(product_id, offer_id=offer_id))


class GoogleMerchantClient:
    def __init__(self, connection: IntegrationConnection):
        if connection.connection_type != IntegrationConnection.TYPE_GOOGLE_MERCHANT:
            raise GoogleMerchantIntegrationError('Connection is not configured for Google Merchant.')

        self.connection = connection
        self.metadata = connection.metadata or {}
        self.account_id = str(self.metadata.get('account_id') or '').strip()
        if not self.account_id:
            raise GoogleMerchantIntegrationError('Google Merchant account_id is required in connection metadata.')

        self.data_source = self._resolve_data_source()
        self.content_language = str(self.metadata.get('content_language') or 'en').strip() or 'en'
        self.feed_label = str(self.metadata.get('feed_label') or self.metadata.get('target_country') or 'KE').strip() or 'KE'
        self.base_url = (connection.base_url or DEFAULT_MERCHANT_API_BASE_URL).rstrip('/')
        self.timeout = int(getattr(settings, 'GOOGLE_MERCHANT_TIMEOUT_SECONDS', 30))

    def _resolve_data_source(self) -> str:
        data_source = str(self.metadata.get('data_source') or self.metadata.get('data_source_name') or '').strip()
        if data_source:
            return data_source

        data_source_id = str(self.metadata.get('data_source_id') or '').strip()
        if data_source_id:
            return f'accounts/{self.account_id}/dataSources/{data_source_id}'

        raise GoogleMerchantIntegrationError('Google Merchant data_source or data_source_id is required in connection metadata.')

    def _access_token(self) -> str:
        if self.connection.auth_type == IntegrationConnection.AUTH_BEARER:
            token = self._env_value('ACCESS_TOKEN') or self.connection.resolve_api_secret()
            if not token:
                raise GoogleMerchantIntegrationError('Google Merchant bearer access token is required.')
            return token

        service_account_info = self._service_account_info()
        try:
            from google.auth.transport.requests import Request as GoogleAuthRequest
            from google.oauth2 import service_account
        except ImportError as exc:
            raise GoogleMerchantIntegrationError('google-auth is required for Google Merchant service account authentication.') from exc

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=[GOOGLE_MERCHANT_SCOPE],
        )
        credentials.refresh(GoogleAuthRequest())
        if not credentials.token:
            raise GoogleMerchantIntegrationError('Google Merchant service account did not return an access token.')
        return credentials.token

    def _service_account_info(self) -> dict[str, Any]:
        raw_json = self._env_value('SERVICE_ACCOUNT_JSON') or self.metadata.get('service_account_json')
        if raw_json:
            if isinstance(raw_json, dict):
                return raw_json
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError as exc:
                raise GoogleMerchantIntegrationError('Google Merchant service account JSON is invalid.') from exc

        file_path = self._env_value('SERVICE_ACCOUNT_FILE') or self.metadata.get('service_account_file')
        if file_path:
            try:
                with open(file_path, encoding='utf-8') as handle:
                    return json.load(handle)
            except OSError as exc:
                raise GoogleMerchantIntegrationError(f'Could not read Google Merchant service account file: {exc}') from exc
            except json.JSONDecodeError as exc:
                raise GoogleMerchantIntegrationError('Google Merchant service account file is invalid JSON.') from exc

        raise GoogleMerchantIntegrationError('Google Merchant service account JSON or file path is required.')

    def _env_value(self, suffix: str) -> str:
        prefix = (self.connection.secret_env_prefix or '').strip().upper()
        if not prefix:
            return ''
        return os.environ.get(f'{prefix}_{suffix}', '') or ''

    def _headers(self) -> dict[str, str]:
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._access_token()}',
        }

    def _request(self, path: str, *, method: str = 'GET', query: dict[str, Any] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f'{self.base_url}{path}'
        if query:
            url = f'{url}?{urlencode(query)}'
        body = json.dumps(data).encode('utf-8') if data is not None else None
        request = Request(url=url, data=body, headers=self._headers(), method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                content = response.read().decode('utf-8')
                return json.loads(content) if content else {}
        except HTTPError as exc:
            body = exc.read().decode('utf-8', errors='ignore')
            raise GoogleMerchantIntegrationError(f'Google Merchant HTTP {exc.code}: {body or exc.reason}') from exc
        except URLError as exc:
            raise GoogleMerchantIntegrationError(f'Could not reach Google Merchant: {exc.reason}') from exc
        except Exception as exc:
            raise GoogleMerchantIntegrationError(f'Google Merchant request failed: {exc}') from exc

    def insert_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            f'/products/v1/accounts/{quote(self.account_id)}/productInputs:insert',
            method='POST',
            query={'dataSource': self.data_source},
            data=payload,
        )

    def delete_product(self, *, content_language: str, feed_label: str, offer_id: str) -> dict[str, Any]:
        identifier = quote(f'{content_language}~{feed_label}~{offer_id}', safe='')
        return self._request(
            f'/products/v1/accounts/{quote(self.account_id)}/productInputs/{identifier}',
            method='DELETE',
            query={'dataSource': self.data_source},
        )


class GoogleMerchantSyncService:
    def __init__(self, connection: IntegrationConnection):
        self.connection = connection
        self.client = GoogleMerchantClient(connection)

    def sync_product(self, product_id: int) -> dict[str, Any]:
        Product = apps.get_model('catalogue', 'Product')
        product = (
            Product.objects.filter(id=product_id)
            .prefetch_related('stockrecords', 'categories', 'images', 'attribute_values__attribute')
            .first()
        )
        if product is None:
            return {'status': 'missing', 'product_id': product_id}

        offer_id = self.offer_id_for_product(product)
        sync_record, _ = GoogleMerchantProductSync.objects.update_or_create(
            connection=self.connection,
            product=product,
            defaults={
                'offer_id': offer_id,
                'content_language': self.client.content_language,
                'feed_label': self.client.feed_label,
                'status': GoogleMerchantProductSync.STATUS_PENDING,
                'last_action': GoogleMerchantProductSync.ACTION_INSERT,
                'last_error': '',
            },
        )
        job = self._start_job(SyncJob.TYPE_PRODUCTS_IMPORT, direction=SyncJob.DIRECTION_OUTBOUND)

        try:
            payload, skip_reason = self.build_product_input(product)
            if skip_reason:
                deleted_response = self._delete_existing_product_input(sync_record)
                sync_record.status = GoogleMerchantProductSync.STATUS_SKIPPED
                sync_record.last_action = GoogleMerchantProductSync.ACTION_SKIP
                sync_record.last_payload = payload
                sync_record.last_response = {'reason': skip_reason, 'deleted_existing_input': bool(deleted_response), 'delete_response': deleted_response or {}}
                sync_record.last_error = ''
                sync_record.synced_at = timezone.now()
                sync_record.save(update_fields=['status', 'last_action', 'last_payload', 'last_response', 'last_error', 'synced_at', 'updated_at'])
                self._finish_job(job, SyncJob.STATUS_SUCCEEDED, {'status': 'skipped', 'reason': skip_reason})
                self._log(job, 'product', offer_id, SyncEventLog.STATUS_PROCESSED, {'status': 'skipped', 'reason': skip_reason})
                return {'status': 'skipped', 'reason': skip_reason, 'product_id': product.id}

            response = self.client.insert_product(payload)
        except GoogleMerchantIntegrationError as exc:
            sync_record.status = GoogleMerchantProductSync.STATUS_FAILED
            sync_record.last_error = str(exc)
            sync_record.save(update_fields=['status', 'last_error', 'updated_at'])
            self._finish_job(job, SyncJob.STATUS_FAILED, {'status': 'failed'}, error=str(exc))
            self._log(job, 'product', offer_id, SyncEventLog.STATUS_FAILED, error=str(exc))
            raise

        sync_record.status = GoogleMerchantProductSync.STATUS_SYNCED
        sync_record.last_action = GoogleMerchantProductSync.ACTION_INSERT
        sync_record.last_payload = payload
        sync_record.last_response = response
        sync_record.product_input_name = response.get('name') or ''
        sync_record.processed_product_name = response.get('product') or ''
        sync_record.last_error = ''
        sync_record.synced_at = timezone.now()
        sync_record.save(
            update_fields=[
                'status',
                'last_action',
                'last_payload',
                'last_response',
                'product_input_name',
                'processed_product_name',
                'last_error',
                'synced_at',
                'updated_at',
            ]
        )
        self.connection.last_successful_sync_at = timezone.now()
        self.connection.save(update_fields=['last_successful_sync_at', 'updated_at'])
        self._finish_job(job, SyncJob.STATUS_SUCCEEDED, {'status': 'synced', 'product_id': product.id, 'offer_id': offer_id})
        self._log(job, 'product', offer_id, SyncEventLog.STATUS_PROCESSED, response)
        return {'status': 'synced', 'product_id': product.id, 'offer_id': offer_id}

    def delete_product(self, product_id: int, offer_id: str = '') -> dict[str, Any]:
        sync_record = GoogleMerchantProductSync.objects.filter(connection=self.connection, product_id=product_id).first()
        if sync_record:
            offer_id = offer_id or sync_record.offer_id
            content_language = sync_record.content_language
            feed_label = sync_record.feed_label
        else:
            content_language = self.client.content_language
            feed_label = self.client.feed_label

        if not offer_id:
            return {'status': 'skipped', 'reason': 'No offer id known for deleted product.', 'product_id': product_id}

        job = self._start_job(SyncJob.TYPE_PRODUCTS_IMPORT, direction=SyncJob.DIRECTION_OUTBOUND)
        try:
            response = self.client.delete_product(content_language=content_language, feed_label=feed_label, offer_id=offer_id)
        except GoogleMerchantIntegrationError as exc:
            if sync_record:
                sync_record.status = GoogleMerchantProductSync.STATUS_FAILED
                sync_record.last_action = GoogleMerchantProductSync.ACTION_DELETE
                sync_record.last_error = str(exc)
                sync_record.save(update_fields=['status', 'last_action', 'last_error', 'updated_at'])
            self._finish_job(job, SyncJob.STATUS_FAILED, {'status': 'failed'}, error=str(exc))
            self._log(job, 'product', offer_id, SyncEventLog.STATUS_FAILED, error=str(exc))
            raise

        if sync_record:
            sync_record.status = GoogleMerchantProductSync.STATUS_DELETED
            sync_record.last_action = GoogleMerchantProductSync.ACTION_DELETE
            sync_record.last_response = response
            sync_record.last_error = ''
            sync_record.synced_at = timezone.now()
            sync_record.save(update_fields=['status', 'last_action', 'last_response', 'last_error', 'synced_at', 'updated_at'])
        self._finish_job(job, SyncJob.STATUS_SUCCEEDED, {'status': 'deleted', 'product_id': product_id, 'offer_id': offer_id})
        self._log(job, 'product', offer_id, SyncEventLog.STATUS_PROCESSED, response)
        return {'status': 'deleted', 'product_id': product_id, 'offer_id': offer_id}

    def _delete_existing_product_input(self, sync_record: GoogleMerchantProductSync) -> dict[str, Any] | None:
        if sync_record.status not in {GoogleMerchantProductSync.STATUS_SYNCED, GoogleMerchantProductSync.STATUS_FAILED}:
            return None
        try:
            return self.client.delete_product(
                content_language=sync_record.content_language,
                feed_label=sync_record.feed_label,
                offer_id=sync_record.offer_id,
            )
        except GoogleMerchantIntegrationError as exc:
            message = str(exc)
            if 'HTTP 404' in message or 'NOT_FOUND' in message:
                return {'status': 'already_missing'}
            raise

    def build_product_input(self, product) -> tuple[dict[str, Any], str]:
        offer_id = self.offer_id_for_product(product)
        payload = {
            'offerId': offer_id,
            'contentLanguage': self.client.content_language,
            'feedLabel': self.client.feed_label,
            'productAttributes': {},
        }

        if not getattr(product, 'is_public', False):
            return payload, 'Product is draft or hidden.'

        stockrecord = product.stockrecords.first()
        price = stockrecord_price(stockrecord)
        currency = stockrecord_currency(stockrecord)
        image_link = self._absolute_image_url(product)

        missing = []
        if not product.title:
            missing.append('title')
        if not product.description:
            missing.append('description')
        if price is None:
            missing.append('price')
        if not image_link:
            missing.append('image')
        if missing:
            return payload, f'Missing required Google Merchant fields: {", ".join(missing)}.'

        attributes = {
            'title': product.title[:150],
            'description': self._plain_description(product.description),
            'link': self._product_link(product),
            'imageLink': image_link,
            'availability': 'IN_STOCK' if self._available_stock(product) > 0 else 'OUT_OF_STOCK',
            'price': {
                'amountMicros': self._amount_micros(price),
                'currencyCode': currency,
            },
            'condition': 'NEW',
        }
        brand = product_brand(product)
        if brand:
            attributes['brand'] = brand[:70]
        product_type = self._product_type(product)
        if product_type:
            attributes['productTypes'] = [product_type[:750]]

        payload['productAttributes'] = attributes
        return payload, ''

    def offer_id_for_product(self, product) -> str:
        return str(getattr(product, 'upc', '') or f'product-{product.id}').strip()[:255]

    def _available_stock(self, product) -> int:
        return sum(stockrecord_count(stockrecord) for stockrecord in product.stockrecords.all())

    def _amount_micros(self, amount: Any) -> str:
        try:
            value = Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise GoogleMerchantIntegrationError('Product price is not a valid decimal amount.') from exc
        return str(int((value * Decimal('1000000')).quantize(Decimal('1'))))

    def _plain_description(self, description: str) -> str:
        return ' '.join(str(description or '').split())[:5000]

    def _product_link(self, product) -> str:
        base_url = (self.client.metadata.get('storefront_base_url') or settings.STOREFRONT_BASE_URL).rstrip('/')
        return f'{base_url}/products/{product.id}'

    def _absolute_image_url(self, product) -> str:
        try:
            image = product.primary_image()
        except TypeError:
            image = product.primary_image
        except Exception:
            image = None
        if not image or not getattr(image, 'original', None):
            return ''
        url = image.original.url or ''
        if url.startswith(('http://', 'https://')):
            return url
        base_url = (self.client.metadata.get('backend_public_base_url') or settings.BACKEND_PUBLIC_BASE_URL).rstrip('/')
        return f'{base_url}{url if url.startswith("/") else f"/{url}"}'

    def _product_type(self, product) -> str:
        categories = list(product.categories.all())
        if not categories:
            return ''
        categories.sort(key=lambda category: (getattr(category, 'depth', 0), getattr(category, 'name', '')))
        return ' > '.join(category.name for category in categories if category.name)

    def _start_job(self, job_type: str, *, direction: str) -> SyncJob:
        return SyncJob.objects.create(
            connection=self.connection,
            job_type=job_type,
            direction=direction,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
        )

    def _finish_job(self, job: SyncJob, status: str, summary: dict[str, Any], error: str = '') -> None:
        job.status = status
        job.summary = summary
        job.error_message = error
        job.finished_at = timezone.now()
        job.save(update_fields=['status', 'summary', 'error_message', 'finished_at'])
        if status == SyncJob.STATUS_FAILED:
            self.connection.last_failed_sync_at = timezone.now()
            self.connection.save(update_fields=['last_failed_sync_at', 'updated_at'])

    def _log(self, job: SyncJob, entity_type: str, reference: str, status: str, payload: dict[str, Any] | None = None, error: str = '') -> None:
        SyncEventLog.objects.create(
            connection=self.connection,
            job=job,
            direction=SyncJob.DIRECTION_OUTBOUND,
            entity_type=entity_type,
            external_reference=reference,
            status=status,
            payload_excerpt=sanitize_metadata(payload or {}),
            error_message=error,
        )


def sync_product_to_active_google_merchant_connections(product_id: int) -> list[dict[str, Any]]:
    results = []
    for connection in active_google_merchant_connections():
        results.append(GoogleMerchantSyncService(connection).sync_product(product_id))
    return results


def delete_product_from_active_google_merchant_connections(product_id: int, offer_id: str = '') -> list[dict[str, Any]]:
    results = []
    for connection in active_google_merchant_connections():
        results.append(GoogleMerchantSyncService(connection).delete_product(product_id, offer_id=offer_id))
    return results


def refresh_all_google_merchant_products() -> dict[str, Any]:
    Product = apps.get_model('catalogue', 'Product')
    product_ids = list(Product.objects.exclude(structure='parent').values_list('id', flat=True))
    synced = 0
    for product_id in product_ids:
        sync_product_to_active_google_merchant_connections(product_id)
        synced += 1
    return {'products_checked': len(product_ids), 'sync_calls': synced}
