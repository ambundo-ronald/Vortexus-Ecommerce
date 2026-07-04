import json
import logging
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger(__name__)


class ProductDomainRouter:
    PRODUCT_CLASS_MAP = {
        'filter': {'category': 'filter', 'collection': 'Filter'},
        'filters': {'category': 'filter', 'collection': 'Filter'},
        'controller': {'category': 'controller', 'collection': 'controller'},
        'controllers': {'category': 'controller', 'collection': 'controller'},
        'surfacepump': {'category': 'surface pumps', 'collection': 'SurfacePump'},
        'surface_pump': {'category': 'surface pumps', 'collection': 'SurfacePump'},
        'surface pump': {'category': 'surface pumps', 'collection': 'SurfacePump'},
        'surface pumps': {'category': 'surface pumps', 'collection': 'SurfacePump'},
        'submersiblepump': {'category': 'submersible pumps', 'collection': 'SubmersiblePump'},
        'submersible_pump': {'category': 'submersible pumps', 'collection': 'SubmersiblePump'},
        'submersible pump': {'category': 'submersible pumps', 'collection': 'SubmersiblePump'},
        'submersible pumps': {'category': 'submersible pumps', 'collection': 'SubmersiblePump'},
        'blower': {'category': 'blower', 'collection': 'Blower'},
        'blowers': {'category': 'blower', 'collection': 'Blower'},
        'chemical': {'category': 'chemical', 'collection': 'Chemical'},
        'chemicals': {'category': 'chemical', 'collection': 'Chemical'},
        'desalinationsystem': {'category': 'desalination systems', 'collection': 'desalinationsystem'},
        'desalination_system': {'category': 'desalination systems', 'collection': 'desalinationsystem'},
        'desalination system': {'category': 'desalination systems', 'collection': 'desalinationsystem'},
        'desalination systems': {'category': 'desalination systems', 'collection': 'desalinationsystem'},
        'flowmeter': {'category': 'flow meter', 'collection': 'flowmeter'},
        'flow_meter': {'category': 'flow meter', 'collection': 'flowmeter'},
        'flow meter': {'category': 'flow meter', 'collection': 'flowmeter'},
        'flow meters': {'category': 'flow meter', 'collection': 'flowmeter'},
        'plumbingfitting': {'category': 'plumbing fittings', 'collection': 'plumbingfitting'},
        'plumbing_fitting': {'category': 'plumbing fittings', 'collection': 'plumbingfitting'},
        'plumbing fitting': {'category': 'plumbing fittings', 'collection': 'plumbingfitting'},
        'plumbing fittings': {'category': 'plumbing fittings', 'collection': 'plumbingfitting'},
        'sterilizer': {'category': 'sterilizer', 'collection': 'sterilizer'},
        'sterilizers': {'category': 'sterilizer', 'collection': 'sterilizer'},
        'vessel': {'category': 'vessel', 'collection': 'vessel'},
        'vessels': {'category': 'vessel', 'collection': 'vessel'},
    }

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self.base_url = (base_url if base_url is not None else getattr(settings, 'PRODUCT_MICROSERVICE_BASE_URL', '')).rstrip('/')
        self.timeout = timeout if timeout is not None else int(getattr(settings, 'PRODUCT_MICROSERVICE_TIMEOUT_SECONDS', 8))

    @classmethod
    def normalize_product_class(cls, value: str | None) -> str:
        return str(value or '').strip().lower().replace('-', '_')

    @classmethod
    def resolve_domain(cls, product_class: str | None) -> dict | None:
        normalized = cls.normalize_product_class(product_class)
        return cls.PRODUCT_CLASS_MAP.get(normalized) or cls.PRODUCT_CLASS_MAP.get(normalized.replace('_', ' '))

    def create(self, *, product, product_class: str, specs: dict, stockrecord=None) -> dict:
        domain = self._require_domain(product_class)
        payload = self._build_payload(product=product, domain=domain, specs=specs, stockrecord=stockrecord)
        response = self._request('POST', '/api/v1/products', payload)
        return self._result(response=response, domain=domain, payload=payload)

    def update(self, *, mongo_id: str, product, product_class: str, specs: dict, stockrecord=None) -> dict:
        domain = self._require_domain(product_class)
        payload = self._build_payload(product=product, domain=domain, specs=specs, stockrecord=stockrecord)
        response = self._request('PATCH', f'/api/v1/products/{mongo_id}', payload)
        return self._result(response=response, domain=domain, payload=payload)

    def get(self, mongo_id: str) -> dict:
        return self._request('GET', f'/api/v1/products/{mongo_id}')

    def delete(self, mongo_id: str) -> dict:
        return self._request('DELETE', f'/api/v1/products/{mongo_id}')

    def _require_domain(self, product_class: str | None) -> dict:
        domain = self.resolve_domain(product_class)
        if not domain:
            raise serializers.ValidationError({'product_class': 'Unsupported Mongo product class.'})
        return domain

    def _build_payload(self, *, product, domain: dict, specs: dict, stockrecord=None) -> dict:
        specs = specs or {}
        payload = {
            **specs,
            'name': specs.get('name') or product.title,
            'description': specs.get('description') or product.description or product.title,
            'category': domain['category'],
            'status': 'active' if product.is_public else 'draft',
            'meta': {
                'title': product.meta_title or product.title,
                'description': product.meta_description or product.description or '',
                **(specs.get('meta') or {}),
            },
            'django_product_id': product.id,
            'django_upc': product.upc,
        }
        if stockrecord is not None:
            price = getattr(stockrecord, 'price', None)
            payload.setdefault('min_price', self._json_value(price))
            payload.setdefault('max_price', self._json_value(price))
            payload.setdefault('in_stock', bool((getattr(stockrecord, 'num_in_stock', 0) or 0) > 0))
        return self._json_value(payload)

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        if not self.base_url:
            raise serializers.ValidationError({'domain_specs': 'PRODUCT_MICROSERVICE_BASE_URL is not configured.'})

        data = None
        headers = {'Accept': 'application/json'}
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')
            headers['Content-Type'] = 'application/json'

        request = Request(f'{self.base_url}{path}', data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode('utf-8')
        except HTTPError as exc:
            detail = exc.read().decode('utf-8', errors='ignore')
            logger.warning('Product microservice %s %s failed: %s', method, path, detail)
            raise serializers.ValidationError({'domain_specs': f'Product microservice rejected the request: {detail or exc.reason}'}) from exc
        except URLError as exc:
            logger.warning('Product microservice %s %s unavailable: %s', method, path, exc)
            raise serializers.ValidationError({'domain_specs': 'Product microservice is unavailable.'}) from exc

        return json.loads(body or '{}')

    def _result(self, *, response: dict, domain: dict, payload: dict) -> dict:
        product = (response.get('data') or {}).get('product') or response.get('product') or response
        mongo_id = product.get('_id') or product.get('id')
        if not mongo_id:
            raise serializers.ValidationError({'domain_specs': 'Product microservice response did not include a Mongo id.'})
        return {
            'mongo_id': str(mongo_id),
            'collection': domain['collection'],
            'payload': product or payload,
        }

    def _json_value(self, value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {key: self._json_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_value(item) for item in value]
        return value
