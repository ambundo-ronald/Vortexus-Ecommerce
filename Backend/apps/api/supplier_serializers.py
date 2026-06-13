from django.apps import apps
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.template.defaultfilters import slugify
from django.utils import timezone
from rest_framework import serializers

from apps.common.products import serialize_product_card

from .serializers import ProductWriteSerializer


class SupplierProfileSerializer(serializers.Serializer):
    def to_representation(self, supplier_profile):
        partner = supplier_profile.partner
        user = supplier_profile.user
        return {
            'id': supplier_profile.id,
            'status': supplier_profile.status,
            'company_name': supplier_profile.company_name,
            'contact_name': supplier_profile.contact_name,
            'phone': supplier_profile.phone,
            'country_code': supplier_profile.country_code,
            'website': supplier_profile.website,
            'notes': supplier_profile.notes,
            'status_note': supplier_profile.status_note,
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'code': partner.code,
            },
            'account_manager': {
                'id': supplier_profile.account_manager_id,
                'email': supplier_profile.account_manager.email,
                'name': supplier_profile.account_manager.get_full_name() or supplier_profile.account_manager.username or supplier_profile.account_manager.email,
            } if supplier_profile.account_manager else None,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
            },
            'created_at': supplier_profile.created_at,
            'updated_at': supplier_profile.updated_at,
        }


class SupplierProfileWriteSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=255)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    country_code = serializers.CharField(required=False, allow_blank=True, max_length=2)
    website = serializers.URLField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
        Partner = apps.get_model('partner', 'Partner')

        user = self.context['request'].user
        cleaned = self.validated_data

        supplier_profile = getattr(user, 'supplier_profile', None)
        company_name = cleaned['company_name'].strip()

        if supplier_profile is None:
            partner_code = self._build_partner_code(company_name)
            partner = Partner.objects.create(code=partner_code, name=company_name)
            supplier_profile = SupplierProfile.objects.create(
                user=user,
                partner=partner,
                company_name=company_name,
                contact_name=cleaned.get('contact_name', '').strip(),
                phone=cleaned.get('phone', '').strip(),
                country_code=(cleaned.get('country_code', '') or '').strip().upper(),
                website=cleaned.get('website', '').strip(),
                notes=cleaned.get('notes', '').strip(),
            )
            return supplier_profile

        dirty_fields = []
        for field in ('company_name', 'contact_name', 'phone', 'website', 'notes'):
            if field in cleaned:
                value = cleaned.get(field, '').strip()
                if getattr(supplier_profile, field) != value:
                    setattr(supplier_profile, field, value)
                    dirty_fields.append(field)

        if 'country_code' in cleaned:
            country_code = (cleaned.get('country_code', '') or '').strip().upper()
            if supplier_profile.country_code != country_code:
                supplier_profile.country_code = country_code
                dirty_fields.append('country_code')

        if dirty_fields:
            supplier_profile.save(update_fields=dirty_fields)

        if supplier_profile.partner.name != supplier_profile.company_name:
            supplier_profile.partner.name = supplier_profile.company_name
            supplier_profile.partner.save(update_fields=['name'])

        return supplier_profile

    @staticmethod
    def _build_partner_code(company_name: str) -> str:
        Partner = apps.get_model('partner', 'Partner')

        base = slugify(company_name).replace('-', '_')[:128] or 'supplier'
        candidate = base
        suffix = 1
        while Partner.objects.filter(code=candidate).exists():
            suffix += 1
            candidate = f'{base[:120]}_{suffix}'
        return candidate[:128]


class SupplierAdminStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['pending', 'approved', 'suspended'])
    account_manager_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    company_name = serializers.CharField(required=False, max_length=255)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    country_code = serializers.CharField(required=False, allow_blank=True, max_length=2)
    website = serializers.URLField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    status_note = serializers.CharField(required=False, allow_blank=True)

    def validate_account_manager_id(self, value):
        if value is None:
            return None
        User = get_user_model()
        try:
            return User.objects.get(id=value, is_staff=True)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError('Choose an active staff user as account manager.') from exc

    def update(self, instance, validated_data):
        dirty_fields = []

        account_manager = validated_data.pop('account_manager_id', serializers.empty)
        if account_manager is not serializers.empty and instance.account_manager_id != getattr(account_manager, 'id', None):
            instance.account_manager = account_manager
            dirty_fields.append('account_manager')

        for field in ('status', 'company_name', 'contact_name', 'phone', 'website', 'notes', 'status_note'):
            if field in validated_data:
                value = validated_data[field].strip() if isinstance(validated_data[field], str) else validated_data[field]
                if getattr(instance, field) != value:
                    setattr(instance, field, value)
                    dirty_fields.append(field)

        if 'country_code' in validated_data:
            country_code = (validated_data.get('country_code') or '').strip().upper()
            if instance.country_code != country_code:
                instance.country_code = country_code
                dirty_fields.append('country_code')

        if dirty_fields:
            instance.save(update_fields=dirty_fields)

        if 'company_name' in dirty_fields and instance.partner.name != instance.company_name:
            instance.partner.name = instance.company_name
            instance.partner.save(update_fields=['name'])

        return instance


class SupplierDashboardSerializer(serializers.Serializer):
    def to_representation(self, supplier_profile):
        Product = apps.get_model('catalogue', 'Product')
        StockRecord = apps.get_model('partner', 'StockRecord')
        partner = supplier_profile.partner

        stockrecords = StockRecord.objects.filter(partner=partner).select_related('product')
        product_ids = stockrecords.values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids).exclude(structure='parent').distinct()
        SupplierProductSubmission = apps.get_model('marketplace', 'SupplierProductSubmission')

        return {
            'supplier': SupplierProfileSerializer(supplier_profile).data,
            'metrics': {
                'product_count': products.count(),
                'stockrecord_count': stockrecords.count(),
                'public_product_count': products.filter(is_public=True).count(),
                'pending_product_count': SupplierProductSubmission.objects.filter(
                    supplier=supplier_profile,
                    status=SupplierProductSubmission.STATUS_PENDING_REVIEW,
                ).count(),
                'low_stock_count': stockrecords.filter(num_in_stock__lte=5).count(),
                'inventory_units': stockrecords.aggregate(total=Sum('num_in_stock')).get('total') or 0,
            },
        }


class SupplierProductWriteSerializer(ProductWriteSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs.pop('partner_id', None)
        attrs.pop('partner_name', None)
        attrs.pop('is_public', None)
        return attrs

    def create(self, validated_data):
        validated_data['is_public'] = False
        product = super().create(validated_data)
        self._mark_pending_review(product)
        return product

    def update(self, instance, validated_data):
        validated_data['is_public'] = False
        product = super().update(instance, validated_data)
        self._mark_pending_review(product)
        return product

    def _resolve_partner(self, product, payload):
        supplier_profile = self.context['supplier_profile']
        return supplier_profile.partner

    def _mark_pending_review(self, product):
        SupplierProductSubmission = apps.get_model('marketplace', 'SupplierProductSubmission')
        supplier_profile = self.context['supplier_profile']
        user = self.context['request'].user
        submission, _ = SupplierProductSubmission.objects.update_or_create(
            product=product,
            defaults={
                'supplier': supplier_profile,
                'status': SupplierProductSubmission.STATUS_PENDING_REVIEW,
                'submitted_by': user,
                'reviewed_by': None,
                'reviewed_at': None,
                'review_note': '',
            },
        )
        if product.is_public:
            product.is_public = False
            product.save(update_fields=['is_public'])
        return submission


class SupplierProductListSerializer(serializers.Serializer):
    @staticmethod
    def build_offer(product, supplier_profile):
        stockrecord = (
            product.stockrecords.select_related('partner')
            .filter(partner=supplier_profile.partner)
            .order_by('id')
            .first()
        )
        return {
            'stockrecord_id': stockrecord.id if stockrecord else None,
            'partner_sku': stockrecord.partner_sku if stockrecord else '',
            'price': stockrecord.price if stockrecord else None,
            'currency': stockrecord.price_currency if stockrecord else '',
            'num_in_stock': stockrecord.num_in_stock if stockrecord else 0,
        }

    @staticmethod
    def build_moderation(product, supplier_profile):
        submission = getattr(product, 'supplier_submission', None)
        if submission is None:
            fallback_status = 'approved' if product.is_public else 'pending_review'
            return {
                'status': fallback_status,
                'review_note': '',
                'submitted_at': None,
                'reviewed_at': None,
                'reviewed_by': None,
            }
        return {
            'id': submission.id,
            'status': submission.status,
            'review_note': submission.review_note,
            'supplier_note': submission.supplier_note,
            'submitted_at': submission.submitted_at,
            'reviewed_at': submission.reviewed_at,
            'reviewed_by': {
                'id': submission.reviewed_by_id,
                'email': submission.reviewed_by.email,
            } if submission.reviewed_by else None,
        }

    def to_representation(self, product):
        supplier_profile = self.context['supplier_profile']
        item = serialize_product_card(product, display_currency=None)
        item['supplier'] = {
            'partner_id': supplier_profile.partner.id,
            'partner_name': supplier_profile.partner.name,
            'partner_code': supplier_profile.partner.code,
            'status': supplier_profile.status,
        }
        item['offer'] = self.build_offer(product, supplier_profile)
        item['moderation'] = self.build_moderation(product, supplier_profile)
        item['shared_catalog'] = product.stockrecords.exclude(partner=supplier_profile.partner).exists()
        return item


class SupplierProductModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['approved', 'rejected', 'changes_requested', 'suspended', 'pending_review']
    )
    review_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        status_value = attrs['status']
        review_note = (attrs.get('review_note') or '').strip()
        if status_value in {'rejected', 'changes_requested', 'suspended'} and not review_note:
            raise serializers.ValidationError({'review_note': 'A review note is required for this decision.'})
        attrs['review_note'] = review_note
        return attrs

    def update(self, instance, validated_data):
        status_value = validated_data['status']
        review_note = validated_data.get('review_note', '')
        user = self.context['request'].user
        product = instance.product

        instance.status = status_value
        instance.review_note = review_note
        instance.reviewed_by = user
        instance.reviewed_at = timezone.now()
        instance.save(update_fields=['status', 'review_note', 'reviewed_by', 'reviewed_at', 'updated_at'])

        should_be_public = status_value == instance.STATUS_APPROVED
        if product.is_public != should_be_public:
            product.is_public = should_be_public
            product.save(update_fields=['is_public'])

        return instance


class SupplierProductModerationListSerializer(serializers.Serializer):
    def to_representation(self, submission):
        supplier = submission.supplier
        product = submission.product
        return {
            'id': submission.id,
            'status': submission.status,
            'review_note': submission.review_note,
            'supplier_note': submission.supplier_note,
            'submitted_at': submission.submitted_at,
            'reviewed_at': submission.reviewed_at,
            'supplier': SupplierProfileSerializer(supplier).data,
            'product': serialize_product_card(product, display_currency=None),
            'reviewed_by': {
                'id': submission.reviewed_by_id,
                'email': submission.reviewed_by.email,
            } if submission.reviewed_by else None,
        }
