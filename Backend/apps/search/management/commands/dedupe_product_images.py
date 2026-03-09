import hashlib

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Remove duplicate product images per product using SHA256 content hash.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upc',
            dest='upc',
            help='Optional single product UPC to clean.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without deleting files/rows.',
        )

    def handle(self, *args, **options):
        Product = apps.get_model('catalogue', 'Product')
        queryset = Product.objects.order_by('id')

        upc = options.get('upc')
        if upc:
            queryset = queryset.filter(upc=upc)
            if not queryset.exists():
                raise CommandError(f'No product found for upc={upc}')

        stats = {
            'products_scanned': 0,
            'products_with_duplicates': 0,
            'duplicates_found': 0,
            'images_deleted': 0,
            'hash_errors': 0,
        }

        for product in queryset:
            stats['products_scanned'] += 1
            images = list(product.images.all().order_by('display_order', 'id'))
            if len(images) < 2:
                continue

            seen_hashes: dict[str, int] = {}
            duplicates = []

            for image in images:
                digest = self._hash_image(image)
                if not digest:
                    stats['hash_errors'] += 1
                    continue

                if digest in seen_hashes:
                    duplicates.append(image)
                else:
                    seen_hashes[digest] = image.id

            if not duplicates:
                continue

            stats['products_with_duplicates'] += 1
            stats['duplicates_found'] += len(duplicates)

            for duplicate in duplicates:
                self.stdout.write(
                    f"Duplicate image detected: product_upc={product.upc} image_id={duplicate.id} file={duplicate.original.name}"
                )
                if options['dry_run']:
                    continue
                duplicate.delete()
                stats['images_deleted'] += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Image deduplication finished'))
        self.stdout.write(f"Products scanned: {stats['products_scanned']}")
        self.stdout.write(f"Products with duplicates: {stats['products_with_duplicates']}")
        self.stdout.write(f"Duplicate images found: {stats['duplicates_found']}")
        self.stdout.write(f"Images deleted: {stats['images_deleted']}")
        self.stdout.write(f"Hash errors: {stats['hash_errors']}")
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run mode active: no images were deleted.'))

    def _hash_image(self, image) -> str | None:
        file_field = getattr(image, 'original', None)
        if not file_field:
            return None

        sha = hashlib.sha256()
        try:
            file_field.open('rb')
            for chunk in file_field.chunks():
                sha.update(chunk)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'Could not hash image id={image.id}: {exc}'))
            return None
        finally:
            try:
                file_field.close()
            except Exception:
                pass

        return sha.hexdigest()
