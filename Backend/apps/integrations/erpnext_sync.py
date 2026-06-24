import json
import hashlib
import re
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils import timezone

from apps.auditlog.services import sanitize_metadata
from apps.common.currency import convert_amount, normalize_currency_code
from apps.common.media import normalize_uploaded_image

from .models import IntegrationConnection, IntegrationMapping, SyncEventLog, SyncJob
from .services import ERPNextIntegrationError, build_erpnext_client


def _resolve_partner(connection: IntegrationConnection):
    if connection.partner_id:
        return connection.partner

    Partner = apps.get_model('partner', 'Partner')
    name = connection.metadata.get('partner_name') or 'Default Partner'
    code = slugify(name).replace('-', '_')[:128] or 'default_partner'
    partner, _ = Partner.objects.get_or_create(code=code, defaults={'name': name})
    if partner.name != name:
        partner.name = name
        partner.save(update_fields=['name'])
    return partner


def _resolve_product_class(connection: IntegrationConnection):
    ProductClass = apps.get_model('catalogue', 'ProductClass')
    name = connection.metadata.get('product_class') or 'Industrial Product'
    product_class, _ = ProductClass.objects.get_or_create(name=name)
    return product_class


def _normalize_category_segments(group_name: str, groups_by_name: dict[str, dict]) -> list[str]:
    segments: list[str] = []
    seen = set()
    current = groups_by_name.get(group_name)

    while current and current.get('name') not in seen:
        current_name = (current.get('name') or '').strip()
        if current_name and current_name.lower() != 'all item groups':
            segments.append(current_name)
        seen.add(current_name)
        parent_name = (current.get('parent_item_group') or '').strip()
        if not parent_name or parent_name == current_name:
            break
        current = groups_by_name.get(parent_name)

    return list(reversed(segments))


def _get_or_create_category_path(path_segments: list[str]):
    Category = apps.get_model('catalogue', 'Category')
    if not path_segments:
        return None, 0

    created_count = 0
    parent = None
    for segment in path_segments:
        if parent is None:
            node = Category.get_root_nodes().filter(name__iexact=segment).first()
            if not node:
                node = Category.add_root(name=segment, slug=slugify(segment), is_public=True)
                created_count += 1
        else:
            node = parent.get_children().filter(name__iexact=segment).first()
            if not node:
                node = parent.add_child(name=segment, slug=slugify(segment), is_public=True)
                created_count += 1
        parent = node

    return parent, created_count


def _upsert_mapping(connection: IntegrationConnection, entity_type: str, external_id: str, internal_model: str, internal_id: str, metadata: dict | None = None):
    IntegrationMapping.objects.update_or_create(
        connection=connection,
        entity_type=entity_type,
        external_id=external_id,
        defaults={
            'internal_model': internal_model,
            'internal_id': internal_id,
            'metadata': metadata or {},
        },
    )


def _save_attribute(product, product_class, code: str, name: str, value: str):
    ProductAttribute = apps.get_model('catalogue', 'ProductAttribute')
    attribute, _ = ProductAttribute.objects.get_or_create(
        product_class=product_class,
        code=code,
        defaults={
            'name': name,
            'type': ProductAttribute.TEXT,
            'required': False,
        },
    )
    attribute.save_value(product, value)


def _parse_decimal(value, default='0'):
    try:
        return Decimal(str(value if value not in (None, '') else default))
    except Exception:
        return Decimal(str(default))


def _normalise_price_for_marketplace(price: dict | None, default_currency: str) -> tuple[Decimal, str]:
    source_currency = normalize_currency_code((price or {}).get('currency')) or normalize_currency_code(default_currency)
    target_currency = normalize_currency_code(default_currency)
    source_amount = _parse_decimal((price or {}).get('price_list_rate'), default='0')
    converted_amount, output_currency = convert_amount(source_amount, source_currency, target_currency)
    if normalize_currency_code(output_currency) != target_currency:
        return source_amount, source_currency
    return _parse_decimal(converted_amount, default=str(source_amount)), target_currency


def _normalise_stockrecord_for_marketplace(stockrecord, default_currency: str) -> list[str]:
    target_currency = normalize_currency_code(default_currency)
    source_currency = normalize_currency_code(stockrecord.price_currency)
    if not target_currency or source_currency == target_currency:
        return []

    converted_amount, output_currency = convert_amount(stockrecord.price, source_currency, target_currency)
    if normalize_currency_code(output_currency) != target_currency:
        return []

    stockrecord.price = _parse_decimal(converted_amount, default=str(stockrecord.price)).quantize(Decimal('0.01'))
    stockrecord.price_currency = target_currency
    return ['price', 'price_currency']


def _decimal_to_float(value) -> float:
    return float(_parse_decimal(value).quantize(Decimal('0.01')))


def _make_safe_identifier(value: str, max_length: int) -> str:
    normalized = (value or '').strip()
    if len(normalized) <= max_length:
        return normalized
    digest = hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:10]
    prefix_length = max_length - len(digest) - 1
    return f'{normalized[:prefix_length]}-{digest}'


def _first_image_reference(item: dict) -> str:
    for field in ('image', 'website_image', 'thumbnail'):
        value = (item.get(field) or '').strip()
        if value:
            return value
    return ''


def _extract_unpermitted_field(error_message: str) -> str:
    match = re.search(r'Field not permitted in query:\s*([A-Za-z0-9_]+)', error_message or '')
    return match.group(1) if match else ''


def _filename_from_image_reference(image_reference: str, item_code: str) -> str:
    path = urlparse(image_reference).path if image_reference else ''
    filename = Path(path).name or f'{item_code or "erpnext-item"}.jpg'
    if not Path(filename).suffix:
        filename = f'{filename}.jpg'
    return filename


class ERPNextSyncService:
    def __init__(self, connection: IntegrationConnection):
        self.connection = connection
        self.client = build_erpnext_client(connection)
        self.partner = _resolve_partner(connection)
        self.product_class = _resolve_product_class(connection)
        self.default_currency = connection.metadata.get('default_currency') or settings.OSCAR_DEFAULT_CURRENCY
        self.default_price_list = connection.metadata.get('price_list') or getattr(settings, 'ERPNEXT_DEFAULT_PRICE_LIST', 'Standard Selling')
        self.page_length = int(connection.metadata.get('page_length') or getattr(settings, 'ERP_SYNC_PAGE_LENGTH', 1000))
        self.selected_item_groups = {
            str(group).strip()
            for group in connection.metadata.get('item_groups', [])
            if str(group).strip()
        }

    def _log_event(self, job: SyncJob, entity_type: str, status: str, external_reference: str = '', payload_excerpt: dict | None = None, error_message: str = ''):
        SyncEventLog.objects.create(
            connection=self.connection,
            job=job,
            direction=job.direction,
            entity_type=entity_type,
            external_reference=external_reference,
            status=status,
            payload_excerpt=sanitize_metadata(payload_excerpt or {}),
            error_message=error_message,
        )

    def _fetch_item_groups(self) -> list[dict]:
        return self.client.fetch_all(
            '/api/resource/Item Group',
            query={
                'fields': json.dumps(['name', 'parent_item_group', 'is_group', 'modified']),
            },
            page_length=self.page_length,
        )

    def _fetch_items(self) -> list[dict]:
        fields = [
            'name',
            'item_name',
            'description',
            'item_group',
            'stock_uom',
            'disabled',
            'image',
            'website_image',
            'thumbnail',
            'modified',
        ]
        optional_fields = {'image', 'website_image', 'thumbnail'}
        rejected_fields = set()

        while True:
            try:
                return self.client.fetch_all(
                    '/api/resource/Item',
                    query={'fields': json.dumps([field for field in fields if field not in rejected_fields])},
                    page_length=self.page_length,
                )
            except ERPNextIntegrationError as exc:
                rejected_field = _extract_unpermitted_field(str(exc))
                if rejected_field not in optional_fields or rejected_field in rejected_fields:
                    raise
                rejected_fields.add(rejected_field)

    def _fetch_prices(self) -> list[dict]:
        return self.client.fetch_all(
            '/api/resource/Item Price',
            query={
                'fields': json.dumps(['name', 'item_code', 'price_list', 'currency', 'price_list_rate', 'modified']),
            },
            page_length=self.page_length,
        )

    def _fetch_bins(self) -> list[dict]:
        return self.client.fetch_all(
            '/api/resource/Bin',
            query={
                'fields': json.dumps(['name', 'item_code', 'warehouse', 'actual_qty', 'reserved_qty', 'modified']),
            },
            page_length=self.page_length,
        )

    def _import_product_image(self, *, product, item: dict, item_code: str, job: SyncJob) -> str:
        image_reference = _first_image_reference(item)
        if not image_reference:
            return 'missing'

        ProductImage = apps.get_model('catalogue', 'ProductImage')
        max_bytes = int(getattr(settings, 'MAX_PRODUCT_IMAGE_BYTES', 10 * 1024 * 1024))
        max_dimension = int(getattr(settings, 'MAX_PRODUCT_IMAGE_DIMENSION', 2400))

        try:
            image_bytes = self.client.fetch_file_bytes(image_reference, max_bytes=max_bytes * 4)
            filename = _filename_from_image_reference(image_reference, item_code)
            upload = SimpleUploadedFile(filename, image_bytes)
            normalized = normalize_uploaded_image(upload, max_bytes=max_bytes, max_dimension=max_dimension)
            if hasattr(normalized, 'seek'):
                normalized.seek(0)
            normalized_bytes = normalized.read()
            image_hash = hashlib.sha256(normalized_bytes).hexdigest()

            existing_hashes = set()
            for image in product.images.all():
                original = getattr(image, 'original', None)
                if not original:
                    continue
                try:
                    with original.open('rb') as handle:
                        existing_hashes.add(hashlib.sha256(handle.read()).hexdigest())
                except Exception:
                    continue

            if image_hash in existing_hashes:
                return 'duplicate'

            product_image = ProductImage(
                product=product,
                caption=(item.get('item_name') or item_code).strip(),
                display_order=product.images.count(),
            )
            product_image.original.save(getattr(normalized, 'name', filename), ContentFile(normalized_bytes), save=False)
            product_image.save()
            return 'created'
        except Exception as exc:
            self._log_event(
                job,
                entity_type='product_image',
                status=SyncEventLog.STATUS_FAILED,
                external_reference=item_code,
                payload_excerpt={'image': image_reference},
                error_message=str(exc),
            )
            return 'failed'

    def import_catalog(self, actor=None, include_stock: bool = True) -> dict:
        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_PRODUCTS_IMPORT,
            direction=SyncJob.DIRECTION_INBOUND,
            status=SyncJob.STATUS_RUNNING,
            created_by=actor,
            started_at=timezone.now(),
        )
        summary = {
            'categories_created': 0,
            'products_created': 0,
            'products_updated': 0,
            'stock_created': 0,
            'stock_updated': 0,
            'images_created': 0,
            'images_duplicate': 0,
            'images_missing': 0,
            'images_failed': 0,
        }

        try:
            groups = self._fetch_item_groups()
            items = self._fetch_items()
            prices = self._fetch_prices()
            summary['item_groups_fetched'] = len(groups)
            summary['items_fetched'] = len(items)
            summary['prices_fetched'] = len(prices)
            price_map = {}
            for price in prices:
                if price.get('price_list') != self.default_price_list:
                    continue
                price_map[price.get('item_code')] = price

            groups_by_name = {group.get('name'): group for group in groups if group.get('name')}
            Product = apps.get_model('catalogue', 'Product')
            StockRecord = apps.get_model('partner', 'StockRecord')
            product_upc_max_length = Product._meta.get_field('upc').max_length or 64
            partner_sku_max_length = StockRecord._meta.get_field('partner_sku').max_length or 128
            existing_product_mappings = {
                mapping.external_id: mapping
                for mapping in IntegrationMapping.objects.filter(
                    connection=self.connection,
                    entity_type=IntegrationMapping.ENTITY_PRODUCT,
                )
            }

            with transaction.atomic():
                for item in items:
                    item_code = (item.get('name') or '').strip()
                    if not item_code:
                        continue

                    category = None
                    item_group = (item.get('item_group') or '').strip()
                    if self.selected_item_groups and item_group not in self.selected_item_groups:
                        continue

                    if item_group:
                        segments = _normalize_category_segments(item_group, groups_by_name)
                        category, created_count = _get_or_create_category_path(segments)
                        summary['categories_created'] += created_count
                        if category:
                            _upsert_mapping(
                                self.connection,
                                IntegrationMapping.ENTITY_CATEGORY,
                                item_group,
                                'catalogue.Category',
                                str(category.id),
                                {'path': segments},
                            )

                    mapping = existing_product_mappings.get(item_code)
                    safe_upc = _make_safe_identifier(item_code, product_upc_max_length)
                    product_defaults = {
                        'upc': safe_upc,
                        'title': (item.get('item_name') or item_code).strip(),
                        'description': (item.get('description') or '').strip(),
                        'is_public': not bool(item.get('disabled')),
                        'product_class': self.product_class,
                        'structure': getattr(Product, 'STANDALONE', 'standalone'),
                    }
                    created = False
                    if mapping:
                        product = Product.objects.filter(id=mapping.internal_id).first()
                        if product is None:
                            mapping = None
                            existing_product_mappings.pop(item_code, None)
                    if mapping is None:
                        product, created = Product.objects.get_or_create(upc=safe_upc, defaults=product_defaults)
                        if created:
                            summary['products_created'] += 1
                    else:
                        dirty = []
                        title = (item.get('item_name') or item_code).strip()
                        description = (item.get('description') or '').strip()
                        is_public = not bool(item.get('disabled'))
                        if product.title != title:
                            product.title = title
                            dirty.append('title')
                        if (product.description or '') != description:
                            product.description = description
                            dirty.append('description')
                        if product.is_public != is_public:
                            product.is_public = is_public
                            dirty.append('is_public')
                        if product.product_class_id != self.product_class.id:
                            product.product_class = self.product_class
                            dirty.append('product_class')
                        if product.upc != safe_upc:
                            product.upc = safe_upc
                            dirty.append('upc')
                        if dirty:
                            product.save(update_fields=dirty)
                            summary['products_updated'] += 1

                    if category:
                        product.categories.set([category])

                    _upsert_mapping(
                        self.connection,
                        IntegrationMapping.ENTITY_PRODUCT,
                        item_code,
                        'catalogue.Product',
                        str(product.id),
                        {'item_group': item_group, 'category_id': category.id if category else None, 'safe_upc': safe_upc},
                    )
                    existing_product_mappings[item_code] = IntegrationMapping(
                        connection=self.connection,
                        entity_type=IntegrationMapping.ENTITY_PRODUCT,
                        external_id=item_code,
                        internal_model='catalogue.Product',
                        internal_id=str(product.id),
                    )

                    stockrecord = product.stockrecords.filter(partner=self.partner).first()
                    created_stock = stockrecord is None
                    if stockrecord is None:
                        stockrecord = StockRecord(product=product, partner=self.partner)

                    price = price_map.get(item_code)
                    stockrecord.partner_sku = _make_safe_identifier(item_code, partner_sku_max_length)
                    normalised_price, normalised_currency = _normalise_price_for_marketplace(price, self.default_currency)
                    stockrecord.price_currency = normalised_currency
                    stockrecord.price = normalised_price
                    if include_stock and created_stock:
                        stockrecord.num_in_stock = 0
                    stockrecord.save()

                    if created_stock:
                        summary['stock_created'] += 1
                    else:
                        summary['stock_updated'] += 1

                    stock_uom = (item.get('stock_uom') or '').strip()
                    if stock_uom:
                        _save_attribute(product, self.product_class, 'stock_uom', 'Stock UOM', stock_uom)
                    if item_group:
                        _save_attribute(product, self.product_class, 'erpnext_item_group', 'ERPNext Item Group', item_group)

                    image_result = self._import_product_image(product=product, item=item, item_code=item_code, job=job)
                    if image_result == 'created':
                        summary['images_created'] += 1
                    elif image_result == 'duplicate':
                        summary['images_duplicate'] += 1
                    elif image_result == 'missing':
                        summary['images_missing'] += 1
                    else:
                        summary['images_failed'] += 1

                    self._log_event(
                        job,
                        entity_type='product',
                        status=SyncEventLog.STATUS_PROCESSED,
                        external_reference=item_code,
                        payload_excerpt={'title': product.title, 'item_group': item_group, 'image': _first_image_reference(item)},
                    )

                if include_stock:
                    stock_summary = self.sync_stock(actor=actor, existing_job=job)
                    summary['stock_synced_items'] = stock_summary['stock_synced_items']

                job.status = SyncJob.STATUS_SUCCEEDED
                job.finished_at = timezone.now()
                job.summary = summary
                job.save(update_fields=['status', 'finished_at', 'summary'])
                self.connection.status = IntegrationConnection.STATUS_ACTIVE
                self.connection.last_successful_sync_at = timezone.now()
                self.connection.save(update_fields=['status', 'last_successful_sync_at', 'updated_at'])
            return summary
        except ERPNextIntegrationError as exc:
            self.connection.status = IntegrationConnection.STATUS_ERROR
            self.connection.last_failed_sync_at = timezone.now()
            self.connection.save(update_fields=['status', 'last_failed_sync_at', 'updated_at'])
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = summary
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='catalog_import', status=SyncEventLog.STATUS_FAILED, error_message=str(exc))
            raise

    def sync_stock(self, actor=None, existing_job: SyncJob | None = None) -> dict:
        job = existing_job or SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_STOCK_IMPORT,
            direction=SyncJob.DIRECTION_INBOUND,
            status=SyncJob.STATUS_RUNNING,
            created_by=actor,
            started_at=timezone.now(),
        )
        created_job = existing_job is None
        summary = {'stock_synced_items': 0}

        try:
            bins = self._fetch_bins()
            summary['bins_fetched'] = len(bins)
            stock_by_item = defaultdict(lambda: Decimal('0'))
            for row in bins:
                item_code = (row.get('item_code') or '').strip()
                warehouse = (row.get('warehouse') or '').strip()
                if not item_code:
                    continue
                if self.connection.default_warehouse and warehouse and warehouse != self.connection.default_warehouse:
                    continue
                stock_by_item[item_code] += _parse_decimal(row.get('actual_qty'), default='0')

            Product = apps.get_model('catalogue', 'Product')
            StockRecord = apps.get_model('partner', 'StockRecord')
            mappings = IntegrationMapping.objects.filter(
                connection=self.connection,
                entity_type=IntegrationMapping.ENTITY_PRODUCT,
                external_id__in=list(stock_by_item.keys()),
            )
            mapped_product_ids = [mapping.internal_id for mapping in mappings]
            mapping_by_external_id = {mapping.external_id: mapping for mapping in mappings}
            products = Product.objects.filter(id__in=mapped_product_ids).prefetch_related('stockrecords')
            products_by_id = {str(product.id): product for product in products}

            with transaction.atomic():
                for external_id, mapping in mapping_by_external_id.items():
                    product = products_by_id.get(str(mapping.internal_id))
                    if product is None:
                        continue
                    qty = int(stock_by_item.get(external_id, Decimal('0')))
                    stockrecord = product.stockrecords.filter(partner=self.partner).first()
                    if stockrecord is None:
                        stockrecord = StockRecord.objects.create(
                            product=product,
                            partner=self.partner,
                            partner_sku=_make_safe_identifier(external_id, StockRecord._meta.get_field('partner_sku').max_length or 128),
                            price_currency=self.default_currency,
                            price=Decimal('0'),
                            num_in_stock=qty,
                        )
                    else:
                        update_fields = _normalise_stockrecord_for_marketplace(stockrecord, self.default_currency)
                        if stockrecord.num_in_stock != qty:
                            stockrecord.num_in_stock = qty
                            update_fields.append('num_in_stock')
                        if update_fields:
                            stockrecord.save(update_fields=update_fields)
                    summary['stock_synced_items'] += 1
                    self._log_event(
                        job,
                        entity_type='stock',
                        status=SyncEventLog.STATUS_PROCESSED,
                        external_reference=external_id,
                        payload_excerpt={'num_in_stock': qty},
                    )

                if created_job:
                    job.status = SyncJob.STATUS_SUCCEEDED
                    job.finished_at = timezone.now()
                    job.summary = summary
                    job.save(update_fields=['status', 'finished_at', 'summary'])
                self.connection.status = IntegrationConnection.STATUS_ACTIVE
                self.connection.last_successful_sync_at = timezone.now()
                self.connection.save(update_fields=['status', 'last_successful_sync_at', 'updated_at'])
            return summary
        except ERPNextIntegrationError as exc:
            self.connection.status = IntegrationConnection.STATUS_ERROR
            self.connection.last_failed_sync_at = timezone.now()
            self.connection.save(update_fields=['status', 'last_failed_sync_at', 'updated_at'])
            if created_job:
                job.status = SyncJob.STATUS_FAILED
                job.finished_at = timezone.now()
                job.error_message = str(exc)
                job.summary = summary
                job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='stock', status=SyncEventLog.STATUS_FAILED, error_message=str(exc))
            raise

    def export_order(self, order) -> dict:
        existing_mapping = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            internal_model='order.Order',
            internal_id=str(order.id),
        ).first()
        if existing_mapping:
            return {
                'status': 'already_exported',
                'order_number': order.number,
                'erpnext_sales_order': existing_mapping.external_id,
            }

        if self.connection.metadata.get('use_vortexus_bridge_app') is True:
            return self.export_order_via_bridge(order)

        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_ORDERS_EXPORT,
            direction=SyncJob.DIRECTION_OUTBOUND,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
            summary={'order_number': order.number},
        )
        try:
            payload = self._build_sales_order_payload(order)
            resource = self.client.create_resource('Sales Order', payload)
            sales_order_name = resource.get('name') or order.number

            _upsert_mapping(
                self.connection,
                IntegrationMapping.ENTITY_ORDER,
                sales_order_name,
                'order.Order',
                str(order.id),
                {
                    'order_number': order.number,
                    'exported_at': timezone.now().isoformat(),
                    'customer': payload.get('customer', ''),
                    'item_count': len(payload.get('items', [])),
                },
            )
            self._log_event(
                job,
                entity_type='order',
                status=SyncEventLog.STATUS_PROCESSED,
                external_reference=sales_order_name,
                payload_excerpt={'order_number': order.number, 'items': len(payload.get('items', []))},
            )
            summary = {'order_number': order.number, 'erpnext_sales_order': sales_order_name, 'items_exported': len(payload.get('items', []))}
            job.status = SyncJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.summary = summary
            job.save(update_fields=['status', 'finished_at', 'summary'])
            return {'status': 'exported', **summary}
        except ERPNextIntegrationError as exc:
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = {'order_number': order.number}
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='order', status=SyncEventLog.STATUS_FAILED, external_reference=order.number, error_message=str(exc))
            raise

    def export_order_via_bridge(self, order) -> dict:
        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_ORDERS_EXPORT,
            direction=SyncJob.DIRECTION_OUTBOUND,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
            summary={'order_number': order.number, 'bridge_app': True},
        )
        try:
            payload = self._build_bridge_sales_order_payload(order)
            response = self.client.call_method(
                'vortexus_ecommerce_integration.api.order.create_sales_order',
                {'payload': payload},
            ) or {}
            sales_order_name = response.get('sales_order') or order.number

            _upsert_mapping(
                self.connection,
                IntegrationMapping.ENTITY_ORDER,
                sales_order_name,
                'order.Order',
                str(order.id),
                {
                    'order_number': order.number,
                    'exported_at': timezone.now().isoformat(),
                    'customer': payload.get('customer', ''),
                    'item_count': len(payload.get('items', [])),
                    'bridge_app': True,
                },
            )
            self._log_event(
                job,
                entity_type='order',
                status=SyncEventLog.STATUS_PROCESSED,
                external_reference=sales_order_name,
                payload_excerpt={'order_number': order.number, 'items': len(payload.get('items', [])), 'bridge_app': True},
            )
            summary = {
                'order_number': order.number,
                'erpnext_sales_order': sales_order_name,
                'items_exported': len(payload.get('items', [])),
                'bridge_app': True,
            }
            job.status = SyncJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.summary = summary
            job.save(update_fields=['status', 'finished_at', 'summary'])
            return {'status': 'exported', **summary}
        except ERPNextIntegrationError as exc:
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = {'order_number': order.number, 'bridge_app': True}
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='order', status=SyncEventLog.STATUS_FAILED, external_reference=order.number, error_message=str(exc))
            raise

    def _build_sales_order_payload(self, order) -> dict:
        lines = list(order.lines.select_related('product').order_by('id'))
        item_codes = self._order_item_codes(lines)
        delivery_date = (timezone.localdate() + timedelta(days=int(self.connection.metadata.get('delivery_days') or 7))).isoformat()
        customer = self.connection.metadata.get('default_customer') or self._order_customer_name(order)
        payload = {
            'customer': customer,
            'transaction_date': timezone.localdate().isoformat(),
            'delivery_date': delivery_date,
            'currency': order.currency,
            'po_no': order.number,
            'items': [],
            'remarks': f'Vortexus web order {order.number}',
        }
        if self.connection.default_company:
            payload['company'] = self.connection.default_company

        for line in lines:
            item_code = item_codes.get(str(line.product_id)) or line.partner_sku or line.upc
            if not item_code:
                raise ERPNextIntegrationError(f'Order line {line.id} does not have an ERPNext item code, partner SKU, or UPC.')
            quantity = int(line.quantity or 0)
            if quantity <= 0:
                continue
            unit_rate = _parse_decimal(getattr(line, 'unit_price_incl_tax', None), default='0')
            if unit_rate <= Decimal('0') and line.line_price_incl_tax:
                unit_rate = _parse_decimal(line.line_price_incl_tax) / Decimal(quantity)
            payload['items'].append(
                {
                    'item_code': item_code,
                    'qty': quantity,
                    'rate': _decimal_to_float(unit_rate),
                    'delivery_date': delivery_date,
                    'description': line.title or item_code,
                }
            )

        if not payload['items']:
            raise ERPNextIntegrationError(f'Order {order.number} has no exportable lines.')
        return payload

    def _build_bridge_sales_order_payload(self, order) -> dict:
        payload = self._build_sales_order_payload(order)
        payment = self._order_payment_session(order)
        payload.update(
            {
                'order_id': str(order.id),
                'order_number': order.number,
                'warehouse': self.connection.default_warehouse or self.connection.metadata.get('default_warehouse', ''),
                'selling_price_list': self.default_price_list,
                'submit': self.connection.metadata.get('submit_sales_orders', True),
            }
        )
        if payment:
            payload.update(
                {
                    'payment_provider': payment.provider or payment.method,
                    'payment_reference': payment.external_reference or payment.reference,
                }
            )
        return payload

    def _order_item_codes(self, lines) -> dict[str, str]:
        product_ids = [str(line.product_id) for line in lines if line.product_id]
        if not product_ids:
            return {}
        mappings = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_PRODUCT,
            internal_model='catalogue.Product',
            internal_id__in=product_ids,
        )
        return {str(mapping.internal_id): mapping.external_id for mapping in mappings}

    def _order_customer_name(self, order) -> str:
        user = getattr(order, 'user', None)
        if user:
            mapped_customer = IntegrationMapping.objects.filter(
                connection=self.connection,
                entity_type=IntegrationMapping.ENTITY_CUSTOMER,
                internal_model='auth.User',
                internal_id=str(user.id),
            ).first()
            if mapped_customer:
                return mapped_customer.external_id
            full_name = (user.get_full_name() or '').strip() if callable(getattr(user, 'get_full_name', None)) else ''
            if full_name:
                return full_name
            email = (getattr(user, 'email', '') or '').strip()
            if email:
                return email
        return (order.guest_email or '').strip() or 'Vortexus Online Customer'

    def _order_payment_session(self, order):
        manager = getattr(order, 'payment_sessions', None)
        if manager is None:
            return None
        return (
            manager.filter(status__in=['paid', 'authorized'])
            .order_by('-paid_at', '-created_at')
            .first()
            or manager.order_by('-created_at').first()
        )

    def export_paid_order_accounting(self, payment_session) -> dict:
        if self.connection.metadata.get('use_vortexus_bridge_app') is not True:
            return {'status': 'skipped', 'reason': 'vortexus_bridge_app_not_enabled'}
        order = payment_session.order
        if order is None:
            raise ERPNextIntegrationError(f'Payment {payment_session.reference} is not linked to an order.')

        order_mapping = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            internal_model='order.Order',
            internal_id=str(order.id),
        ).first()
        if not order_mapping:
            self.export_order(order)
            order_mapping = IntegrationMapping.objects.filter(
                connection=self.connection,
                entity_type=IntegrationMapping.ENTITY_ORDER,
                internal_model='order.Order',
                internal_id=str(order.id),
            ).first()
        if not order_mapping:
            raise ERPNextIntegrationError(f'Order {order.number} has not been exported to ERPNext.')
        metadata = order_mapping.metadata or {}
        if metadata.get('sales_invoice') and metadata.get('payment_entry'):
            return {
                'status': 'already_exported',
                'order_number': order.number,
                'sales_invoice': metadata.get('sales_invoice'),
                'payment_entry': metadata.get('payment_entry'),
            }

        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_ORDERS_EXPORT,
            direction=SyncJob.DIRECTION_OUTBOUND,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
            summary={'order_number': order.number, 'payment_reference': payment_session.reference, 'accounting': True},
        )
        try:
            payload = {
                'order_id': str(order.id),
                'order_number': order.number,
                'sales_order': order_mapping.external_id,
                'payment_provider': payment_session.provider or payment_session.method,
                'payment_reference': payment_session.external_reference or payment_session.reference,
                'paid_amount': _decimal_to_float(payment_session.amount),
                'bank_account': self.connection.metadata.get('pesapal_bank_account') or self.connection.metadata.get('default_bank_account', ''),
                'posting_date': (payment_session.paid_at.date() if payment_session.paid_at else timezone.localdate()).isoformat(),
                'create_payment_entry': True,
                'submit': self.connection.metadata.get('submit_sales_invoices', True),
            }
            response = self.client.call_method(
                'vortexus_ecommerce_integration.api.order.create_sales_invoice',
                {'payload': payload},
            ) or {}
            metadata = {
                **metadata,
                'sales_invoice': response.get('sales_invoice', ''),
                'payment_entry': response.get('payment_entry', ''),
                'accounting_exported_at': timezone.now().isoformat(),
            }
            order_mapping.metadata = metadata
            order_mapping.save(update_fields=['metadata', 'updated_at'])
            self._log_event(
                job,
                entity_type='payment',
                status=SyncEventLog.STATUS_PROCESSED,
                external_reference=payload['payment_reference'],
                payload_excerpt={
                    'order_number': order.number,
                    'sales_invoice': metadata.get('sales_invoice', ''),
                    'payment_entry': metadata.get('payment_entry', ''),
                },
            )
            summary = {'order_number': order.number, 'sales_invoice': metadata.get('sales_invoice', ''), 'payment_entry': metadata.get('payment_entry', '')}
            job.status = SyncJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.summary = summary
            job.save(update_fields=['status', 'finished_at', 'summary'])
            return {'status': 'exported', **summary}
        except ERPNextIntegrationError as exc:
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = {'order_number': order.number, 'payment_reference': payment_session.reference, 'accounting': True}
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='payment', status=SyncEventLog.STATUS_FAILED, external_reference=payment_session.reference, error_message=str(exc))
            raise

    def sync_order_cancellation(self, order, *, reason: str = '') -> dict:
        if self.connection.metadata.get('use_vortexus_bridge_app') is not True:
            return {'status': 'skipped', 'reason': 'vortexus_bridge_app_not_enabled'}
        mapping = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            internal_model='order.Order',
            internal_id=str(order.id),
        ).first()
        if not mapping:
            return {'status': 'skipped', 'reason': 'order_not_exported'}

        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_ORDERS_EXPORT,
            direction=SyncJob.DIRECTION_OUTBOUND,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
            summary={'order_number': order.number, 'cancellation': True},
        )
        try:
            response = self.client.call_method(
                'vortexus_ecommerce_integration.api.order.cancel_sales_order',
                {'payload': {'order_id': str(order.id), 'sales_order': mapping.external_id, 'order_number': order.number, 'reason': reason}},
            ) or {}
            mapping.metadata = {**(mapping.metadata or {}), 'cancelled_at': timezone.now().isoformat(), 'cancel_response': response}
            mapping.save(update_fields=['metadata', 'updated_at'])
            self._log_event(job, entity_type='order', status=SyncEventLog.STATUS_PROCESSED, external_reference=mapping.external_id, payload_excerpt={'order_number': order.number, 'cancellation': True})
            job.status = SyncJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.summary = {'order_number': order.number, 'cancelled': True}
            job.save(update_fields=['status', 'finished_at', 'summary'])
            return {'status': 'cancelled', 'order_number': order.number}
        except ERPNextIntegrationError as exc:
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = {'order_number': order.number, 'cancellation': True}
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='order', status=SyncEventLog.STATUS_FAILED, external_reference=mapping.external_id, error_message=str(exc))
            raise

    def export_refund_credit_note(self, payment_session, *, refund_amount: str = '', reason: str = '', refund_reference: str = '') -> dict:
        if self.connection.metadata.get('use_vortexus_bridge_app') is not True:
            return {'status': 'skipped', 'reason': 'vortexus_bridge_app_not_enabled'}
        order = payment_session.order
        if order is None:
            return {'status': 'skipped', 'reason': 'payment_not_linked_to_order'}
        mapping = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_ORDER,
            internal_model='order.Order',
            internal_id=str(order.id),
        ).first()
        if not mapping:
            return {'status': 'skipped', 'reason': 'order_not_exported'}
        metadata = mapping.metadata or {}
        sales_invoice = metadata.get('sales_invoice', '')
        if not sales_invoice:
            return {'status': 'skipped', 'reason': 'sales_invoice_not_exported'}

        effective_refund_reference = refund_reference or f'REFUND-{payment_session.reference}'
        refunds = metadata.get('refunds') or []
        if any(refund.get('refund_reference') == effective_refund_reference for refund in refunds):
            return {'status': 'already_exported', 'refund_reference': effective_refund_reference}

        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_ORDERS_EXPORT,
            direction=SyncJob.DIRECTION_OUTBOUND,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
            summary={'order_number': order.number, 'refund_reference': effective_refund_reference, 'refund': True},
        )
        try:
            payload = {
                'order_id': str(order.id),
                'order_number': order.number,
                'sales_invoice': sales_invoice,
                'payment_provider': payment_session.provider or payment_session.method,
                'payment_reference': payment_session.external_reference or payment_session.reference,
                'refund_reference': effective_refund_reference,
                'refund_amount': refund_amount or str(payment_session.amount),
                'reason': reason or 'Vortexus ecommerce refund.',
                'submit': self.connection.metadata.get('submit_credit_notes', True),
            }
            response = self.client.call_method(
                'vortexus_ecommerce_integration.api.order.create_credit_note',
                {'payload': payload},
            ) or {}
            refunds.append(
                {
                    'refund_reference': effective_refund_reference,
                    'credit_note': response.get('credit_note', ''),
                    'refund_amount': payload['refund_amount'],
                    'exported_at': timezone.now().isoformat(),
                }
            )
            mapping.metadata = {**metadata, 'refunds': refunds}
            mapping.save(update_fields=['metadata', 'updated_at'])
            self._log_event(
                job,
                entity_type='payment',
                status=SyncEventLog.STATUS_PROCESSED,
                external_reference=effective_refund_reference,
                payload_excerpt={'order_number': order.number, 'credit_note': response.get('credit_note', '')},
            )
            summary = {'order_number': order.number, 'refund_reference': effective_refund_reference, 'credit_note': response.get('credit_note', '')}
            job.status = SyncJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.summary = summary
            job.save(update_fields=['status', 'finished_at', 'summary'])
            return {'status': 'exported', **summary}
        except ERPNextIntegrationError as exc:
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = {'order_number': order.number, 'refund_reference': effective_refund_reference, 'refund': True}
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='payment', status=SyncEventLog.STATUS_FAILED, external_reference=effective_refund_reference, error_message=str(exc))
            raise

    def sync_customer(self, user) -> dict:
        existing_mapping = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_CUSTOMER,
            internal_model='auth.User',
            internal_id=str(user.id),
        ).first()

        job = SyncJob.objects.create(
            connection=self.connection,
            job_type=SyncJob.TYPE_CUSTOMERS_IMPORT,
            direction=SyncJob.DIRECTION_OUTBOUND,
            status=SyncJob.STATUS_RUNNING,
            started_at=timezone.now(),
            summary={'user_id': user.id, 'email': user.email},
        )
        try:
            payload = self._build_customer_payload(user)
            if self.connection.metadata.get('use_vortexus_bridge_app') is True:
                response = self.client.call_method(
                    'vortexus_ecommerce_integration.api.customer.upsert_customer',
                    {'payload': payload},
                ) or {}
                customer_name = response.get('customer') or (existing_mapping.external_id if existing_mapping else payload['email'])
            else:
                customer_name = existing_mapping.external_id if existing_mapping else self._create_or_update_customer_resource(payload)

            _upsert_mapping(
                self.connection,
                IntegrationMapping.ENTITY_CUSTOMER,
                customer_name,
                'auth.User',
                str(user.id),
                {
                    'email': user.email,
                    'synced_at': timezone.now().isoformat(),
                    'source': 'ecommerce',
                    'bridge_app': self.connection.metadata.get('use_vortexus_bridge_app') is True,
                },
            )
            self._log_event(
                job,
                entity_type='customer',
                status=SyncEventLog.STATUS_PROCESSED,
                external_reference=customer_name,
                payload_excerpt={'user_id': user.id, 'email': user.email},
            )
            summary = {'user_id': user.id, 'erpnext_customer': customer_name}
            job.status = SyncJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.summary = summary
            job.save(update_fields=['status', 'finished_at', 'summary'])
            return {'status': 'synced', **summary}
        except ERPNextIntegrationError as exc:
            job.status = SyncJob.STATUS_FAILED
            job.finished_at = timezone.now()
            job.error_message = str(exc)
            job.summary = {'user_id': user.id, 'email': user.email}
            job.save(update_fields=['status', 'finished_at', 'error_message', 'summary'])
            self._log_event(job, entity_type='customer', status=SyncEventLog.STATUS_FAILED, external_reference=str(user.id), error_message=str(exc))
            raise

    def _build_customer_payload(self, user) -> dict:
        profile = getattr(user, 'customer_profile', None)
        country_code = (getattr(profile, 'country_code', '') or '').upper()
        country_name = self.connection.metadata.get('default_country') or ('Kenya' if country_code in {'', 'KE'} else country_code)
        return {
            'user_id': str(user.id),
            'email': user.email or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'phone': getattr(profile, 'phone', '') or '',
            'company_name': getattr(profile, 'company', '') or '',
            'customer_group': self.connection.metadata.get('customer_group') or 'Ecommerce',
            'territory': self.connection.metadata.get('territory') or country_name or 'All Territories',
            'billing_address': {
                'address_title': getattr(profile, 'company', '') or user.get_full_name() or user.email,
                'address_line1': self.connection.metadata.get('default_address_line1') or 'Ecommerce Customer',
                'city': self.connection.metadata.get('default_city') or 'Nairobi',
                'country': country_name or 'Kenya',
                'phone': getattr(profile, 'phone', '') or '',
            },
        }

    def _create_or_update_customer_resource(self, payload: dict) -> str:
        existing = IntegrationMapping.objects.filter(
            connection=self.connection,
            entity_type=IntegrationMapping.ENTITY_CUSTOMER,
            internal_model='auth.User',
            internal_id=payload['user_id'],
        ).first()
        if existing:
            return existing.external_id
        resource = self.client.create_resource(
            'Customer',
            {
                'customer_name': payload.get('company_name') or ' '.join(part for part in [payload.get('first_name'), payload.get('last_name')] if part).strip() or payload['email'],
                'customer_type': 'Company' if payload.get('company_name') else 'Individual',
                'customer_group': payload.get('customer_group') or 'Ecommerce',
                'territory': payload.get('territory') or 'All Territories',
            },
        )
        return resource.get('name') or payload['email']


def sync_active_erpnext_stock() -> dict:
    summaries = {'connections_processed': 0, 'stock_synced_items': 0}
    queryset = IntegrationConnection.objects.filter(
        connection_type=IntegrationConnection.TYPE_ERPNEXT,
        is_active=True,
    ).order_by('id')

    for connection in queryset:
        summary = ERPNextSyncService(connection).sync_stock()
        summaries['connections_processed'] += 1
        summaries['stock_synced_items'] += summary['stock_synced_items']
    return summaries


def export_order_to_active_erpnext(order_number: str) -> dict:
    Order = apps.get_model('order', 'Order')
    order = Order.objects.prefetch_related('lines__product').get(number=order_number)
    summaries = {'connections_processed': 0, 'orders_exported': 0, 'orders_skipped': 0}
    queryset = IntegrationConnection.objects.filter(
        connection_type=IntegrationConnection.TYPE_ERPNEXT,
        is_active=True,
    ).order_by('id')

    for connection in queryset:
        if connection.metadata.get('export_orders') is False:
            continue
        result = ERPNextSyncService(connection).export_order(order)
        summaries['connections_processed'] += 1
        if result.get('status') == 'already_exported':
            summaries['orders_skipped'] += 1
        else:
            summaries['orders_exported'] += 1
    return summaries


def sync_customer_to_active_erpnext(user_id: int) -> dict:
    user_app_label, user_model_name = settings.AUTH_USER_MODEL.split('.', 1)
    User = apps.get_model(user_app_label, user_model_name)
    user = User.objects.select_related('customer_profile').get(id=user_id)
    summaries = {'connections_processed': 0, 'customers_synced': 0}
    queryset = IntegrationConnection.objects.filter(
        connection_type=IntegrationConnection.TYPE_ERPNEXT,
        is_active=True,
    ).order_by('id')

    for connection in queryset:
        if connection.metadata.get('sync_customers') is False:
            continue
        ERPNextSyncService(connection).sync_customer(user)
        summaries['connections_processed'] += 1
        summaries['customers_synced'] += 1
    return summaries


def export_paid_order_accounting_to_active_erpnext(payment_reference: str) -> dict:
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    payment = PaymentSession.objects.select_related('order').get(reference=payment_reference)
    summaries = {'connections_processed': 0, 'accounting_exported': 0, 'accounting_skipped': 0}
    if not payment.order_id or payment.status not in {'paid', 'authorized'}:
        return summaries

    queryset = IntegrationConnection.objects.filter(
        connection_type=IntegrationConnection.TYPE_ERPNEXT,
        is_active=True,
    ).order_by('id')
    for connection in queryset:
        if connection.metadata.get('export_order_accounting') is False:
            continue
        result = ERPNextSyncService(connection).export_paid_order_accounting(payment)
        summaries['connections_processed'] += 1
        if result.get('status') == 'skipped':
            summaries['accounting_skipped'] += 1
        else:
            summaries['accounting_exported'] += 1
    return summaries


def sync_order_cancellation_to_active_erpnext(order_number: str, reason: str = '') -> dict:
    Order = apps.get_model('order', 'Order')
    order = Order.objects.get(number=order_number)
    summaries = {'connections_processed': 0, 'orders_cancelled': 0, 'orders_skipped': 0}
    queryset = IntegrationConnection.objects.filter(
        connection_type=IntegrationConnection.TYPE_ERPNEXT,
        is_active=True,
    ).order_by('id')
    for connection in queryset:
        if connection.metadata.get('sync_cancellations') is False:
            continue
        result = ERPNextSyncService(connection).sync_order_cancellation(order, reason=reason)
        summaries['connections_processed'] += 1
        if result.get('status') == 'skipped':
            summaries['orders_skipped'] += 1
        else:
            summaries['orders_cancelled'] += 1
    return summaries


def export_refund_credit_note_to_active_erpnext(payment_reference: str, refund_amount: str = '', reason: str = '', refund_reference: str = '') -> dict:
    PaymentSession = apps.get_model('payments', 'PaymentSession')
    payment = PaymentSession.objects.select_related('order').get(reference=payment_reference)
    summaries = {'connections_processed': 0, 'credit_notes_exported': 0, 'credit_notes_skipped': 0}
    if not payment.order_id:
        return summaries

    queryset = IntegrationConnection.objects.filter(
        connection_type=IntegrationConnection.TYPE_ERPNEXT,
        is_active=True,
    ).order_by('id')
    for connection in queryset:
        if connection.metadata.get('sync_refunds') is False:
            continue
        result = ERPNextSyncService(connection).export_refund_credit_note(
            payment,
            refund_amount=refund_amount,
            reason=reason,
            refund_reference=refund_reference,
        )
        summaries['connections_processed'] += 1
        if result.get('status') == 'skipped':
            summaries['credit_notes_skipped'] += 1
        else:
            summaries['credit_notes_exported'] += 1
    return summaries
