import csv
import hashlib
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from django.apps import apps
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template.defaultfilters import slugify


class Command(BaseCommand):
    help = (
        'Bulk import industrial catalogue data from CSV (upsert by UPC). '
        'Supports dynamic product attributes via columns prefixed with attr__.'
    )

    REQUIRED_COLUMNS = ('upc', 'title')

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file to import.')
        parser.add_argument('--delimiter', default=',', help='CSV delimiter (default: ,).')
        parser.add_argument('--partner', default='Default Partner', help='Partner name for stock records.')
        parser.add_argument(
            '--product-class',
            dest='product_class',
            default='Industrial Product',
            help='Product class name to use/create.',
        )
        parser.add_argument(
            '--default-currency',
            default='USD',
            help='Fallback currency when CSV column currency is empty.',
        )
        parser.add_argument('--dry-run', action='store_true', help='Validate and parse, then rollback changes.')
        parser.add_argument('--fail-fast', action='store_true', help='Stop on first invalid row.')

    def handle(self, *args, **options):
        csv_path = Path(options['csv_file']).expanduser().resolve()
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_path}')
        self.csv_dir = csv_path.parent

        self.Product = apps.get_model('catalogue', 'Product')
        self.Category = apps.get_model('catalogue', 'Category')
        self.ProductClass = apps.get_model('catalogue', 'ProductClass')
        self.ProductAttribute = apps.get_model('catalogue', 'ProductAttribute')
        self.ProductImage = apps.get_model('catalogue', 'ProductImage')
        self.StockRecord = apps.get_model('partner', 'StockRecord')
        self.Partner = apps.get_model('partner', 'Partner')

        product_class = self._get_or_create_product_class(options['product_class'])
        partner = self._get_or_create_partner(options['partner'])

        with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle, delimiter=options['delimiter'])
            if not reader.fieldnames:
                raise CommandError('CSV file has no header row.')

            missing = [column for column in self.REQUIRED_COLUMNS if column not in reader.fieldnames]
            if missing:
                raise CommandError(f'Missing required CSV columns: {", ".join(missing)}')

            if options['dry_run']:
                with transaction.atomic():
                    stats = self._process_rows(
                        reader=reader,
                        product_class=product_class,
                        partner=partner,
                        default_currency=options['default_currency'],
                        fail_fast=options['fail_fast'],
                    )
                    transaction.set_rollback(True)
            else:
                stats = self._process_rows(
                    reader=reader,
                    product_class=product_class,
                    partner=partner,
                    default_currency=options['default_currency'],
                    fail_fast=options['fail_fast'],
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('CSV import finished'))
        self.stdout.write(f"Rows processed: {stats['rows_processed']}")
        self.stdout.write(f"Products created: {stats['products_created']}")
        self.stdout.write(f"Products updated: {stats['products_updated']}")
        self.stdout.write(f"Stock records created: {stats['stock_created']}")
        self.stdout.write(f"Stock records updated: {stats['stock_updated']}")
        self.stdout.write(f"Categories created: {stats['categories_created']}")
        self.stdout.write(f"Attributes created: {stats['attributes_created']}")
        self.stdout.write(f"Images created: {stats['images_created']}")
        self.stdout.write(f"Rows failed: {stats['rows_failed']}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run mode active: all database writes were rolled back.'))

    def _process_rows(self, reader, product_class, partner, default_currency: str, fail_fast: bool) -> dict[str, int]:
        stats = {
            'rows_processed': 0,
            'rows_failed': 0,
            'products_created': 0,
            'products_updated': 0,
            'stock_created': 0,
            'stock_updated': 0,
            'categories_created': 0,
            'attributes_created': 0,
            'images_created': 0,
        }

        for row_number, raw_row in enumerate(reader, start=2):
            row = {
                (key or '').strip(): (value.strip() if isinstance(value, str) else value)
                for key, value in raw_row.items()
            }
            if self._is_empty_row(row):
                continue

            try:
                result = self._upsert_row(
                    row=row,
                    product_class=product_class,
                    partner=partner,
                    default_currency=default_currency,
                )
            except Exception as exc:
                stats['rows_failed'] += 1
                self.stderr.write(self.style.ERROR(f'Row {row_number} failed: {exc}'))
                if fail_fast:
                    raise CommandError(f'Import aborted at row {row_number}: {exc}')
                continue

            stats['rows_processed'] += 1
            stats['products_created'] += int(result['product_created'])
            stats['products_updated'] += int(result['product_updated'])
            stats['stock_created'] += int(result['stock_created'])
            stats['stock_updated'] += int(result['stock_updated'])
            stats['categories_created'] += result['categories_created']
            stats['attributes_created'] += result['attributes_created']
            stats['images_created'] += result['images_created']

        return stats

    def _upsert_row(self, row: dict[str, str], product_class, partner, default_currency: str) -> dict[str, Any]:
        upc = (row.get('upc') or '').strip()
        title = (row.get('title') or '').strip()
        if not upc:
            raise CommandError('Missing upc')
        if not title:
            raise CommandError('Missing title')

        product_defaults = {
            'title': title,
            'description': row.get('description', ''),
            'is_public': self._to_bool(row.get('is_public'), default=True),
            'product_class': product_class,
            'structure': getattr(self.Product, 'STANDALONE', 'standalone'),
        }

        product, product_created = self.Product.objects.get_or_create(upc=upc, defaults=product_defaults)
        product_updated = False

        if not product_created:
            if product.title != title:
                product.title = title
                product_updated = True
            description = row.get('description', '')
            if (product.description or '') != description:
                product.description = description
                product_updated = True
            is_public = self._to_bool(row.get('is_public'), default=True)
            if product.is_public != is_public:
                product.is_public = is_public
                product_updated = True
            if product.product_class_id != product_class.id:
                product.product_class = product_class
                product_updated = True
            if product.structure != getattr(self.Product, 'STANDALONE', 'standalone'):
                product.structure = getattr(self.Product, 'STANDALONE', 'standalone')
                product_updated = True
            if product_updated:
                product.save()

        categories_created = 0
        category_path = (row.get('category_path') or '').strip()
        if category_path:
            category, new_categories = self._get_or_create_category_path(category_path)
            categories_created += new_categories
            if category and not product.categories.filter(id=category.id).exists():
                product.categories.add(category)

        currency = (row.get('currency') or default_currency).strip() or default_currency
        price = self._to_decimal(row.get('price'))
        num_in_stock = self._to_int(row.get('num_in_stock'), default=0)
        partner_sku = (row.get('partner_sku') or upc).strip()

        stockrecord, stock_created = self.StockRecord.objects.get_or_create(
            product=product,
            partner=partner,
            defaults={
                'partner_sku': partner_sku,
                'price_currency': currency,
                'price': price,
                'num_in_stock': num_in_stock,
            },
        )

        stock_updated = False
        if not stock_created:
            if stockrecord.partner_sku != partner_sku:
                stockrecord.partner_sku = partner_sku
                stock_updated = True
            if stockrecord.price_currency != currency:
                stockrecord.price_currency = currency
                stock_updated = True
            if price is not None and stockrecord.price != price:
                stockrecord.price = price
                stock_updated = True
            if stockrecord.num_in_stock != num_in_stock:
                stockrecord.num_in_stock = num_in_stock
                stock_updated = True
            if stock_updated:
                stockrecord.save()

        attributes_created = 0
        for key, value in row.items():
            if not key.startswith('attr__'):
                continue
            if value is None or str(value).strip() == '':
                continue

            code = key.replace('attr__', '', 1).strip().lower()
            if not code:
                continue

            attribute, created = self.ProductAttribute.objects.get_or_create(
                product_class=product_class,
                code=code,
                defaults={
                    'name': code.replace('_', ' ').title(),
                    'type': self.ProductAttribute.TEXT,
                    'required': False,
                },
            )
            if created:
                attributes_created += 1

            attribute.save_value(product, str(value).strip())

        images_created = self._import_images(
            product=product,
            image_path=row.get('image_path'),
            image_paths=row.get('image_paths'),
            image_caption=row.get('image_caption'),
        )

        return {
            'product_created': product_created,
            'product_updated': product_updated,
            'stock_created': stock_created,
            'stock_updated': stock_updated,
            'categories_created': categories_created,
            'attributes_created': attributes_created,
            'images_created': images_created,
        }

    def _import_images(
        self,
        product,
        image_path: str | None,
        image_paths: str | None,
        image_caption: str | None,
    ) -> int:
        entries: list[tuple[Path, str]] = []

        single_path = (image_path or '').strip()
        if single_path:
            entries.append((self._resolve_image_path(single_path), (image_caption or '').strip()))

        raw_multi = (image_paths or '').strip()
        if raw_multi:
            for part in raw_multi.replace(';', '|').split('|'):
                cleaned = part.strip()
                if not cleaned:
                    continue
                entries.append((self._resolve_image_path(cleaned), ''))

        if not entries:
            return 0

        existing_hashes = set()
        for image in product.images.all():
            try:
                with image.original.open('rb') as existing_handle:
                    existing_hashes.add(self._sha256_bytes(existing_handle.read()))
            except Exception:
                continue

        current_display_order = product.images.count()
        created = 0

        for source_path, caption in entries:
            image_bytes = source_path.read_bytes()
            image_hash = self._sha256_bytes(image_bytes)

            if image_hash in existing_hashes:
                continue

            product_image = self.ProductImage(
                product=product,
                caption=caption,
                display_order=current_display_order,
            )
            product_image.original.save(source_path.name, ContentFile(image_bytes), save=False)
            product_image.save()

            existing_hashes.add(image_hash)
            current_display_order += 1
            created += 1

        return created

    def _get_or_create_product_class(self, name: str):
        obj, _ = self.ProductClass.objects.get_or_create(name=name)
        return obj

    def _get_or_create_partner(self, name: str):
        code = slugify(name).replace('-', '_')[:128] or 'default_partner'
        obj, _ = self.Partner.objects.get_or_create(code=code, defaults={'name': name})
        if obj.name != name:
            obj.name = name
            obj.save(update_fields=['name'])
        return obj

    def _get_or_create_category_path(self, path: str):
        segments = [segment.strip() for segment in path.split('>') if segment.strip()]
        if not segments:
            return None, 0

        created_count = 0
        parent = None
        for segment in segments:
            if parent is None:
                node = self.Category.get_root_nodes().filter(name__iexact=segment).first()
                if not node:
                    node = self.Category.add_root(name=segment, slug=slugify(segment), is_public=True)
                    created_count += 1
            else:
                node = parent.get_children().filter(name__iexact=segment).first()
                if not node:
                    node = parent.add_child(name=segment, slug=slugify(segment), is_public=True)
                    created_count += 1
            parent = node

        return parent, created_count

    def _resolve_image_path(self, raw_path: str) -> Path:
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = (self.csv_dir / candidate).resolve()
        else:
            candidate = candidate.resolve()

        if not candidate.exists() or not candidate.is_file():
            raise CommandError(f'Image file not found: {candidate}')

        return candidate

    @staticmethod
    def _sha256_bytes(raw_bytes: bytes) -> str:
        return hashlib.sha256(raw_bytes).hexdigest()

    @staticmethod
    def _to_decimal(raw_value: str | None) -> Decimal | None:
        if raw_value is None or raw_value == '':
            return None
        try:
            return Decimal(raw_value)
        except (InvalidOperation, TypeError) as exc:
            raise CommandError(f'Invalid decimal value: {raw_value}') from exc

    @staticmethod
    def _to_int(raw_value: str | None, default: int = 0) -> int:
        if raw_value is None or raw_value == '':
            return default
        try:
            return int(raw_value)
        except (ValueError, TypeError) as exc:
            raise CommandError(f'Invalid integer value: {raw_value}') from exc

    @staticmethod
    def _to_bool(raw_value: str | None, default: bool = True) -> bool:
        if raw_value is None or raw_value == '':
            return default
        value = str(raw_value).strip().lower()
        if value in {'1', 'true', 't', 'yes', 'y', 'on'}:
            return True
        if value in {'0', 'false', 'f', 'no', 'n', 'off'}:
            return False
        raise CommandError(f'Invalid boolean value: {raw_value}')

    @staticmethod
    def _is_empty_row(row: dict[str, Any]) -> bool:
        return all((value is None or str(value).strip() == '') for value in row.values())
