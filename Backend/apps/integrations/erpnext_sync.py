import json
from collections import defaultdict
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.template.defaultfilters import slugify
from django.utils import timezone

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


class ERPNextSyncService:
    def __init__(self, connection: IntegrationConnection):
        self.connection = connection
        self.client = build_erpnext_client(connection)
        self.partner = _resolve_partner(connection)
        self.product_class = _resolve_product_class(connection)
        self.default_currency = connection.metadata.get('default_currency') or settings.OSCAR_DEFAULT_CURRENCY
        self.default_price_list = connection.metadata.get('price_list') or getattr(settings, 'ERPNEXT_DEFAULT_PRICE_LIST', 'Standard Selling')

    def _log_event(self, job: SyncJob, entity_type: str, status: str, external_reference: str = '', payload_excerpt: dict | None = None, error_message: str = ''):
        SyncEventLog.objects.create(
            connection=self.connection,
            job=job,
            direction=job.direction,
            entity_type=entity_type,
            external_reference=external_reference,
            status=status,
            payload_excerpt=payload_excerpt or {},
            error_message=error_message,
        )

    def _fetch_item_groups(self) -> list[dict]:
        payload = self.client._request(
            '/api/resource/Item Group',
            query={
                'fields': json.dumps(['name', 'parent_item_group', 'is_group', 'modified']),
                'limit_page_length': 1000,
            },
        )
        return payload.get('data') or []

    def _fetch_items(self) -> list[dict]:
        payload = self.client._request(
            '/api/resource/Item',
            query={
                'fields': json.dumps(['name', 'item_name', 'description', 'item_group', 'stock_uom', 'disabled', 'modified']),
                'limit_page_length': 1000,
            },
        )
        return payload.get('data') or []

    def _fetch_prices(self) -> list[dict]:
        payload = self.client._request(
            '/api/resource/Item Price',
            query={
                'fields': json.dumps(['name', 'item_code', 'price_list', 'currency', 'price_list_rate', 'modified']),
                'limit_page_length': 1000,
            },
        )
        return payload.get('data') or []

    def _fetch_bins(self) -> list[dict]:
        payload = self.client._request(
            '/api/resource/Bin',
            query={
                'fields': json.dumps(['name', 'item_code', 'warehouse', 'actual_qty', 'reserved_qty', 'modified']),
                'limit_page_length': 2000,
            },
        )
        return payload.get('data') or []

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
        }

        try:
            groups = self._fetch_item_groups()
            items = self._fetch_items()
            prices = self._fetch_prices()
            price_map = {}
            for price in prices:
                if price.get('price_list') != self.default_price_list:
                    continue
                price_map[price.get('item_code')] = price

            groups_by_name = {group.get('name'): group for group in groups if group.get('name')}
            Product = apps.get_model('catalogue', 'Product')
            StockRecord = apps.get_model('partner', 'StockRecord')

            with transaction.atomic():
                for item in items:
                    item_code = (item.get('name') or '').strip()
                    if not item_code:
                        continue

                    category = None
                    item_group = (item.get('item_group') or '').strip()
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

                    product_defaults = {
                        'title': (item.get('item_name') or item_code).strip(),
                        'description': (item.get('description') or '').strip(),
                        'is_public': not bool(item.get('disabled')),
                        'product_class': self.product_class,
                        'structure': getattr(Product, 'STANDALONE', 'standalone'),
                    }
                    product, created = Product.objects.get_or_create(upc=item_code, defaults=product_defaults)
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
                        {'item_group': item_group, 'category_id': category.id if category else None},
                    )

                    stockrecord = product.stockrecords.filter(partner=self.partner).first()
                    created_stock = stockrecord is None
                    if stockrecord is None:
                        stockrecord = StockRecord(product=product, partner=self.partner)

                    price = price_map.get(item_code)
                    stockrecord.partner_sku = item_code
                    stockrecord.price_currency = (price or {}).get('currency') or self.default_currency
                    stockrecord.price = _parse_decimal((price or {}).get('price_list_rate'), default='0')
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

                    self._log_event(
                        job,
                        entity_type='product',
                        status=SyncEventLog.STATUS_PROCESSED,
                        external_reference=item_code,
                        payload_excerpt={'title': product.title, 'item_group': item_group},
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
            products = Product.objects.filter(upc__in=list(stock_by_item.keys())).prefetch_related('stockrecords')

            with transaction.atomic():
                for product in products:
                    qty = int(stock_by_item.get(product.upc, Decimal('0')))
                    stockrecord = product.stockrecords.filter(partner=self.partner).first()
                    if stockrecord is None:
                        stockrecord = StockRecord.objects.create(
                            product=product,
                            partner=self.partner,
                            partner_sku=product.upc,
                            price_currency=self.default_currency,
                            price=Decimal('0'),
                            num_in_stock=qty,
                        )
                    elif stockrecord.num_in_stock != qty:
                        stockrecord.num_in_stock = qty
                        stockrecord.save(update_fields=['num_in_stock'])
                    summary['stock_synced_items'] += 1
                    self._log_event(
                        job,
                        entity_type='stock',
                        status=SyncEventLog.STATUS_PROCESSED,
                        external_reference=product.upc,
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
