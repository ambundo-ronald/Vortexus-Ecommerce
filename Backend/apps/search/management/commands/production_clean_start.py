import os

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.common.clients import get_opensearch_client


ADMIN_EMAIL = 'norwaengineering8@gmail.com'


class Command(BaseCommand):
    help = (
        'Prepare a clean production start by deleting test users, orders, carts, '
        'payments, logs, analytics, products, categories, suppliers, and catalogue data. '
        'Dry-run by default.'
    )

    deletion_plan = [
        (
            'launch configuration',
            [
                ('payments', 'PaymentProviderConfiguration'),
                ('notifications', 'EmailConfiguration'),
                ('notifications', 'EmailSuppression'),
                ('accounts', 'DeliveryRouteCache'),
                ('accounts', 'DistanceDeliveryMethod'),
                ('shipping', 'WeightBand'),
                ('shipping', 'WeightBased'),
            ],
        ),
        (
            'notifications and logs',
            [
                ('notifications', 'PushDeliveryLog'),
                ('notifications', 'PushSubscription'),
                ('notifications', 'AdminNotification'),
                ('notifications', 'EmailNotification'),
                ('auditlog', 'SearchAnalyticsEvent'),
                ('auditlog', 'AuditLog'),
                ('integrations', 'SyncEventLog'),
                ('integrations', 'SyncJob'),
            ],
        ),
        (
            'payments',
            [
                ('payments', 'PaymentEvent'),
                ('payments', 'PaymentSession'),
            ],
        ),
        (
            'orders, carts, wishlists, and stock reservations',
            [
                ('marketplace', 'SupplierOrderGroup'),
                ('inventory', 'StockReservation'),
                ('wishlists', 'Line'),
                ('wishlists', 'WishList'),
                ('basket', 'Line'),
                ('basket', 'Basket'),
                ('order', 'Order'),
            ],
        ),
        (
            'customer activity',
            [
                ('customer', 'ProductAlert'),
                ('customer', 'ProductView'),
                ('reviews', 'ProductReview'),
            ],
        ),
        (
            'catalogue and suppliers',
            [
                ('marketplace', 'SupplierProductSubmission'),
                ('marketplace', 'SupplierProfile'),
                ('content', 'MarketingMediaAsset'),
                ('content', 'MarketingBlock'),
                ('integrations', 'IntegrationMapping'),
                ('integrations', 'IntegrationConnection'),
                ('accounts', 'ProductMongoReference'),
                ('inventory', 'StockRecordPriceSnapshot'),
                ('partner', 'StockRecord'),
                ('catalogue', 'ProductImage'),
                ('catalogue', 'ProductRecommendation'),
                ('catalogue', 'Product'),
                ('catalogue', 'Category'),
                ('catalogue', 'ProductAttributeValue'),
                ('accounts', 'ProductAttributeMetadata'),
                ('catalogue', 'ProductAttribute'),
                ('catalogue', 'ProductClass'),
                ('partner', 'Partner'),
            ],
        ),
    ]

    backup_record_models = [
        ('backups', 'BackupRestoreRun'),
        ('backups', 'BackupRun'),
    ]

    def add_arguments(self, parser):
        parser.add_argument('--execute', action='store_true', help='Actually delete data. Without this, only a dry-run is shown.')
        parser.add_argument('--admin-email', default=ADMIN_EMAIL, help='The only user email to keep as production admin.')
        parser.add_argument(
            '--admin-password',
            default=os.environ.get('CLEAN_START_ADMIN_PASSWORD', ''),
            help='Password to set if the admin user must be created or reset. Can also use CLEAN_START_ADMIN_PASSWORD.',
        )
        parser.add_argument(
            '--reset-admin-password',
            action='store_true',
            help='Reset the preserved admin password to --admin-password / CLEAN_START_ADMIN_PASSWORD.',
        )
        parser.add_argument(
            '--purge-backup-records',
            action='store_true',
            help='Also delete backup/restore run database records. Backup files on disk are not removed.',
        )
        parser.add_argument(
            '--skip-search-indexes',
            action='store_true',
            help='Do not clear OpenSearch product and image-search indexes.',
        )

    def handle(self, *args, **options):
        admin_email = (options['admin_email'] or '').strip().lower()
        if admin_email != ADMIN_EMAIL:
            raise CommandError(f'Admin email must be {ADMIN_EMAIL!r} for this launch cleanup.')

        execute = bool(options['execute'])
        admin_password = options.get('admin_password') or ''
        reset_admin_password = bool(options['reset_admin_password'])

        admin_user = self._get_admin_user(admin_email)
        if execute and admin_user is None and not admin_password:
            raise CommandError(
                'The preserved admin user does not exist. Provide --admin-password or CLEAN_START_ADMIN_PASSWORD '
                'so the command can create it.'
            )
        if execute and reset_admin_password and not admin_password:
            raise CommandError('--reset-admin-password requires --admin-password or CLEAN_START_ADMIN_PASSWORD.')

        plan = self._build_plan(include_backup_records=options['purge_backup_records'])
        user_delete_count = self._users_to_delete(admin_email).count()

        self.stdout.write(self.style.WARNING('Production clean-start plan'))
        self.stdout.write(f'Mode: {"EXECUTE" if execute else "DRY RUN"}')
        self.stdout.write(f'Preserved admin: {admin_email}')
        self.stdout.write(f'Users to delete: {user_delete_count}')

        for label, model, count in plan:
            self.stdout.write(f'{label}: {model._meta.label} -> {count}')

        if not execute:
            self.stdout.write(self.style.WARNING('Dry-run only. Re-run with --execute to apply this cleanup.'))
            return

        with transaction.atomic():
            admin_user = self._ensure_admin_user(admin_email, admin_password, reset_admin_password)

            for _label, model, _count in plan:
                model.objects.all().delete()

            self._users_to_delete(admin_email).delete()
            self._harden_admin(admin_user, admin_password if reset_admin_password else '')

        if not options['skip_search_indexes']:
            self._clear_search_indexes()

        self.stdout.write(self.style.SUCCESS('Production clean-start completed.'))
        self.stdout.write(self.style.SUCCESS(f'Only preserved admin user should remain: {admin_email}'))

    def _build_plan(self, *, include_backup_records: bool):
        groups = list(self.deletion_plan)
        if include_backup_records:
            groups.append(('backup run records', self.backup_record_models))

        plan = []
        for group_label, model_refs in groups:
            for app_label, model_name in model_refs:
                model = self._model(app_label, model_name)
                if model is None:
                    continue
                plan.append((group_label, model, model.objects.count()))
        return plan

    def _model(self, app_label, model_name):
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            return None

    def _get_admin_user(self, email):
        User = get_user_model()
        return User.objects.filter(email__iexact=email).first()

    def _users_to_delete(self, admin_email):
        User = get_user_model()
        return User.objects.exclude(email__iexact=admin_email)

    def _ensure_admin_user(self, email, password, reset_password):
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            username_field = getattr(User, 'USERNAME_FIELD', 'username')
            create_kwargs = {'email': email}
            if username_field != 'email':
                create_kwargs[username_field] = email
            user = User.objects.create_user(**create_kwargs)

        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        if password and (reset_password or not user.has_usable_password()):
            user.set_password(password)
        user.save()
        return user

    def _harden_admin(self, user, password):
        if password:
            user.set_password(password)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()

    def _clear_search_indexes(self):
        client = get_opensearch_client()
        indexes = [
            getattr(settings, 'SEARCH_INDEX_PRODUCTS', ''),
            getattr(settings, 'SEARCH_INDEX_IMAGE_EMBEDDINGS', ''),
        ]
        for index_name in [index for index in indexes if index]:
            try:
                if not client.indices.exists(index=index_name):
                    continue
                client.delete_by_query(
                    index=index_name,
                    body={'query': {'match_all': {}}},
                    conflicts='proceed',
                    refresh=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Cleared OpenSearch index: {index_name}'))
            except Exception as exc:
                raise CommandError(f'Could not clear OpenSearch index {index_name}: {exc}') from exc
