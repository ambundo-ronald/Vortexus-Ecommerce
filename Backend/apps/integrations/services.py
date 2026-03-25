import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from .models import IntegrationConnection


class ERPNextIntegrationError(Exception):
    pass


@dataclass
class ERPNextPreviewResult:
    resource: str
    count: int
    records: list[dict[str, Any]]


class ERPNextClient:
    def __init__(self, connection: IntegrationConnection):
        if connection.connection_type != IntegrationConnection.TYPE_ERPNEXT:
            raise ERPNextIntegrationError('Connection is not configured for ERPNext.')
        if not connection.base_url:
            raise ERPNextIntegrationError('ERPNext base URL is required.')
        if not connection.api_key or not connection.api_secret:
            raise ERPNextIntegrationError('ERPNext API key and secret are required.')

        self.connection = connection
        self.base_url = connection.base_url.rstrip('/')
        self.timeout = int(getattr(settings, 'ERP_SYNC_TIMEOUT_SECONDS', 30))

    def _headers(self) -> dict[str, str]:
        return {
            'Accept': 'application/json',
            'Authorization': f'token {self.connection.api_key}:{self.connection.api_secret}',
        }

    def _request(self, path: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f'{self.base_url}{quote(path, safe="/")}'
        if query:
            encoded = urlencode(query)
            url = f'{url}?{encoded}'

        request = Request(url=url, headers=self._headers(), method='GET')
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except HTTPError as exc:
            body = exc.read().decode('utf-8', errors='ignore')
            raise ERPNextIntegrationError(f'ERPNext HTTP {exc.code}: {body or exc.reason}') from exc
        except URLError as exc:
            raise ERPNextIntegrationError(f'Could not reach ERPNext: {exc.reason}') from exc
        except Exception as exc:
            raise ERPNextIntegrationError(f'ERPNext request failed: {exc}') from exc

    def test_connection(self) -> dict[str, Any]:
        payload = self._request('/api/method/frappe.auth.get_logged_user')
        user = payload.get('message') or ''
        return {
            'ok': True,
            'erp_user': user,
            'base_url': self.base_url,
            'tested_at': datetime.now(timezone.utc).isoformat(),
        }

    def preview_items(self, limit: int = 20) -> ERPNextPreviewResult:
        payload = self._request(
            '/api/resource/Item',
            query={
                'fields': json.dumps(['name', 'item_name', 'item_group', 'stock_uom', 'disabled', 'modified']),
                'limit_page_length': limit,
            },
        )
        records = payload.get('data') or []
        return ERPNextPreviewResult(resource='items', count=len(records), records=records)

    def preview_stock(self, limit: int = 20) -> ERPNextPreviewResult:
        payload = self._request(
            '/api/resource/Bin',
            query={
                'fields': json.dumps(['name', 'item_code', 'warehouse', 'actual_qty', 'reserved_qty', 'modified']),
                'limit_page_length': limit,
            },
        )
        records = payload.get('data') or []
        return ERPNextPreviewResult(resource='stock', count=len(records), records=records)

    def preview_prices(self, limit: int = 20) -> ERPNextPreviewResult:
        payload = self._request(
            '/api/resource/Item Price',
            query={
                'fields': json.dumps(['name', 'item_code', 'price_list', 'currency', 'price_list_rate', 'modified']),
                'limit_page_length': limit,
            },
        )
        records = payload.get('data') or []
        return ERPNextPreviewResult(resource='prices', count=len(records), records=records)


def build_erpnext_client(connection: IntegrationConnection) -> ERPNextClient:
    return ERPNextClient(connection)
