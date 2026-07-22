from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.template.defaultfilters import slugify
from django.utils import timezone
from rest_framework import serializers

from apps.common.products import serialize_product_card
from apps.common.currency import default_currency

from .serializers import ProductWriteSerializer


ZERO = Decimal('0.00')


def _money(value, default='0.00'):
    return Decimal(str(value if value is not None else default)).quantize(Decimal('0.01'))


def _canonical_stockrecord_for_product(product, exclude_partner_id=None):
    queryset = product.stockrecords.select_related('partner').order_by('id')
    if exclude_partner_id:
        primary = queryset.exclude(partner_id=exclude_partner_id).first()
        if primary:
            return primary
    return queryset.first()


def _supplier_offer_payload(offer):
    product = offer.product
    stockrecord = offer.stockrecord
    return {
        'id': offer.id,
        'status': offer.status,
        'supplier_unit_cost': float(offer.supplier_unit_cost or ZERO),
        'currency': offer.currency or default_currency(),
        'available_quantity': offer.available_quantity,
        'lead_time_days': offer.lead_time_days,
        'supplier_sku': offer.supplier_sku or '',
        'notes': offer.notes or '',
        'review_note': offer.review_note or '',
        'stockrecord_id': offer.stockrecord_id,
        'stock_num_in_stock': stockrecord.num_in_stock if stockrecord else 0,
        'product': serialize_product_card(product, display_currency=None),
        'supplier': SupplierProfileSerializer(offer.supplier).data,
        'submitted_at': offer.submitted_at,
        'reviewed_at': offer.reviewed_at,
        'reviewed_by': {
            'id': offer.reviewed_by_id,
            'email': offer.reviewed_by.email,
        } if offer.reviewed_by else None,
    }


def _supplier_product_request_payload(product_request):
    return {
        'id': product_request.id,
        'status': product_request.status,
        'requested_title': product_request.requested_title,
        'brand': product_request.brand,
        'category_hint': product_request.category_hint,
        'description': product_request.description,
        'specs': product_request.specs or {},
        'supplier_sku': product_request.supplier_sku,
        'supplier_unit_cost': float(product_request.supplier_unit_cost) if product_request.supplier_unit_cost is not None else None,
        'currency': product_request.currency,
        'available_quantity': product_request.available_quantity,
        'notes': product_request.notes,
        'review_note': product_request.review_note,
        'linked_product': serialize_product_card(product_request.linked_product, display_currency=None) if product_request.linked_product else None,
        'supplier': SupplierProfileSerializer(product_request.supplier).data,
        'submitted_at': product_request.submitted_at,
        'reviewed_at': product_request.reviewed_at,
        'reviewed_by': {
            'id': product_request.reviewed_by_id,
            'email': product_request.reviewed_by.email,
        } if product_request.reviewed_by else None,
    }


def apply_supplier_offer_approval(offer, *, reviewer=None, status_value=None, review_note=''):
    SupplierProductOffer = apps.get_model('marketplace', 'SupplierProductOffer')
    StockRecord = apps.get_model('partner', 'StockRecord')

    if status_value:
        offer.status = status_value
    offer.review_note = review_note
    offer.reviewed_by = reviewer
    offer.reviewed_at = timezone.now()

    if offer.status == SupplierProductOffer.STATUS_APPROVED:
        canonical = _canonical_stockrecord_for_product(offer.product, exclude_partner_id=offer.supplier.partner_id)
        selling_price = getattr(canonical, 'price', None) if canonical else ZERO
        selling_currency = getattr(canonical, 'price_currency', None) if canonical else offer.currency or default_currency()
        stockrecord = offer.stockrecord or StockRecord(product=offer.product, partner=offer.supplier.partner)
        stockrecord.partner = offer.supplier.partner
        stockrecord.partner_sku = offer.supplier_sku or offer.product.upc or f'SUP-{offer.product_id}'
        stockrecord.price = selling_price
        stockrecord.price_currency = selling_currency or default_currency()
        stockrecord.num_in_stock = offer.available_quantity
        stockrecord.save()
        offer.stockrecord = stockrecord
    elif offer.stockrecord_id:
        stockrecord = offer.stockrecord
        stockrecord.num_in_stock = 0
        stockrecord.save(update_fields=['num_in_stock'])

    offer.save(update_fields=['status', 'review_note', 'reviewed_by', 'reviewed_at', 'stockrecord', 'updated_at'])
    return offer


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


class SupplierAdminCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(required=False, allow_blank=False, trim_whitespace=False, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    company_name = serializers.CharField(max_length=255)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=40)
    country_code = serializers.CharField(required=False, allow_blank=True, max_length=2)
    website = serializers.URLField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    status_note = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=['pending', 'approved', 'suspended'], default='pending')
    account_manager_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    partner_code = serializers.CharField(required=False, allow_blank=True, max_length=128)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_account_manager_id(self, value):
        if value is None:
            return None
        User = get_user_model()
        try:
            return User.objects.get(id=value, is_staff=True)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError('Choose an active staff user as account manager.') from exc

    def validate_partner_code(self, value):
        partner_code = slugify((value or '').strip()).replace('-', '_')
        if partner_code and len(partner_code) < 2:
            raise serializers.ValidationError('Partner code is too short.')
        return partner_code[:128]

    def validate(self, attrs):
        User = get_user_model()
        email = attrs['email']
        user = User.objects.filter(email__iexact=email).first()
        password = attrs.get('password')

        if user and hasattr(user, 'supplier_profile'):
            raise serializers.ValidationError({'email': 'This user already has a supplier profile.'})
        if user and (user.is_staff or user.is_superuser):
            raise serializers.ValidationError({'email': 'Staff/admin accounts cannot be used as supplier accounts.'})
        if not user and not password:
            raise serializers.ValidationError({'password': 'Password is required when creating a new supplier user.'})
        if password:
            password_validation.validate_password(password, user=user)

        partner_code = attrs.get('partner_code') or self._build_partner_code(attrs['company_name'])
        Partner = apps.get_model('partner', 'Partner')
        if Partner.objects.filter(code__iexact=partner_code).exists():
            raise serializers.ValidationError({'partner_code': 'A partner with this code already exists.'})
        attrs['partner_code'] = partner_code
        attrs['_existing_user'] = user
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        SupplierProfile = apps.get_model('marketplace', 'SupplierProfile')
        Partner = apps.get_model('partner', 'Partner')
        User = get_user_model()

        existing_user = validated_data.pop('_existing_user', None)
        account_manager = validated_data.pop('account_manager_id', None)
        password = validated_data.pop('password', None)
        partner_code = validated_data.pop('partner_code')
        email = validated_data.pop('email')

        company_name = validated_data.pop('company_name').strip()
        first_name = (validated_data.pop('first_name', '') or '').strip()
        last_name = (validated_data.pop('last_name', '') or '').strip()

        if existing_user:
            user = existing_user
            user_dirty_fields = []
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                user_dirty_fields.append('first_name')
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                user_dirty_fields.append('last_name')
            if not user.is_active:
                user.is_active = True
                user_dirty_fields.append('is_active')
            if password:
                user.set_password(password)
                user_dirty_fields.append('password')
            if user_dirty_fields:
                user.save(update_fields=list(dict.fromkeys(user_dirty_fields)))
        else:
            user = User.objects.create_user(
                username=self._generate_username(email),
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            user.save(update_fields=['is_staff', 'is_superuser', 'is_active'])

        partner = Partner.objects.create(code=partner_code, name=company_name)
        if hasattr(partner, 'users'):
            partner.users.add(user)

        supplier_profile = SupplierProfile.objects.create(
            user=user,
            partner=partner,
            company_name=company_name,
            contact_name=(validated_data.get('contact_name') or '').strip(),
            phone=(validated_data.get('phone') or '').strip(),
            country_code=(validated_data.get('country_code') or '').strip().upper(),
            website=(validated_data.get('website') or '').strip(),
            notes=(validated_data.get('notes') or '').strip(),
            status_note=(validated_data.get('status_note') or '').strip(),
            status=validated_data.get('status') or SupplierProfile.STATUS_PENDING,
            account_manager=account_manager,
        )
        return supplier_profile

    @staticmethod
    def _build_partner_code(company_name: str) -> str:
        Partner = apps.get_model('partner', 'Partner')

        base = slugify(company_name).replace('-', '_')[:128] or 'supplier'
        candidate = base
        suffix = 1
        while Partner.objects.filter(code__iexact=candidate).exists():
            suffix += 1
            candidate = f'{base[:120]}_{suffix}'
        return candidate[:128]

    @staticmethod
    def _generate_username(email: str) -> str:
        User = get_user_model()
        base = email.split('@', 1)[0].strip().replace(' ', '_')[:120] or 'supplier'
        candidate = base
        suffix = 1
        while User.objects.filter(username__iexact=candidate).exists():
            suffix += 1
            candidate = f'{base[:140]}_{suffix}'
        return candidate[:150]


class SupplierDashboardSerializer(serializers.Serializer):
    def to_representation(self, supplier_profile):
        Product = apps.get_model('catalogue', 'Product')
        StockRecord = apps.get_model('partner', 'StockRecord')
        SupplierOrderGroup = apps.get_model('marketplace', 'SupplierOrderGroup')
        SupplierProductOffer = apps.get_model('marketplace', 'SupplierProductOffer')
        SupplierOrderLineAllocation = apps.get_model('marketplace', 'SupplierOrderLineAllocation')
        PaymentSession = apps.get_model('payments', 'PaymentSession')
        partner = supplier_profile.partner

        stockrecords = StockRecord.objects.filter(partner=partner).select_related('product')
        product_ids = stockrecords.values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids).exclude(structure='parent').distinct()
        SupplierProductSubmission = apps.get_model('marketplace', 'SupplierProductSubmission')
        supplier_orders = SupplierOrderGroup.objects.filter(partner=partner)
        allocations = SupplierOrderLineAllocation.objects.filter(partner=partner)
        paid_order_ids = PaymentSession.objects.filter(
            order__supplier_groups__partner=partner,
            status__in=[PaymentSession.STATUS_AUTHORIZED, PaymentSession.STATUS_PAID],
        ).values_list('order_id', flat=True)
        paid_supplier_orders = supplier_orders.filter(order_id__in=paid_order_ids)
        paid_allocations = allocations.filter(order_id__in=paid_order_ids)

        return {
            'supplier': SupplierProfileSerializer(supplier_profile).data,
            'metrics': {
                'product_count': products.count(),
                'offer_count': SupplierProductOffer.objects.filter(supplier=supplier_profile).count(),
                'approved_offer_count': SupplierProductOffer.objects.filter(supplier=supplier_profile, status=SupplierProductOffer.STATUS_APPROVED).count(),
                'stockrecord_count': stockrecords.count(),
                'public_product_count': products.filter(is_public=True).count(),
                'pending_product_count': SupplierProductSubmission.objects.filter(
                    supplier=supplier_profile,
                    status=SupplierProductSubmission.STATUS_PENDING_REVIEW,
                ).count(),
                'pending_offer_count': SupplierProductOffer.objects.filter(
                    supplier=supplier_profile,
                    status=SupplierProductOffer.STATUS_PENDING_REVIEW,
                ).count(),
                'low_stock_count': stockrecords.filter(num_in_stock__lte=5).count(),
                'inventory_units': stockrecords.aggregate(total=Sum('num_in_stock')).get('total') or 0,
                'order_count': supplier_orders.count(),
                'open_order_count': supplier_orders.exclude(status__in=['delivered', 'cancelled']).count(),
                'delivered_order_count': supplier_orders.filter(status='delivered').count(),
                'cancelled_order_count': supplier_orders.filter(status='cancelled').count(),
                'gross_sales_total': supplier_orders.aggregate(total=Sum('total_incl_tax')).get('total') or 0,
                'supplier_payable_total': allocations.aggregate(total=Sum('supplier_total_cost')).get('total') or 0,
                'confirmed_payment_total': paid_supplier_orders.aggregate(total=Sum('total_incl_tax')).get('total') or 0,
                'confirmed_payable_total': paid_allocations.aggregate(total=Sum('supplier_total_cost')).get('total') or 0,
                'pending_payment_total': supplier_orders.exclude(order_id__in=paid_order_ids).aggregate(total=Sum('total_incl_tax')).get('total') or 0,
            },
            'payments': {
                'basis': 'confirmed_customer_payment',
                'status': 'settlement_pending',
                'confirmed_total': paid_allocations.aggregate(total=Sum('supplier_total_cost')).get('total') or 0,
                'pending_total': allocations.exclude(order_id__in=paid_order_ids).aggregate(total=Sum('supplier_total_cost')).get('total') or 0,
                'paid_out_total': 0,
            },
        }


class SupplierProductOfferWriteSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    supplier_unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(required=False, allow_blank=True, max_length=12)
    available_quantity = serializers.IntegerField(min_value=0)
    lead_time_days = serializers.IntegerField(required=False, min_value=0, default=0)
    supplier_sku = serializers.CharField(required=False, allow_blank=True, max_length=128)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_product_id(self, value):
        Product = apps.get_model('catalogue', 'Product')
        try:
            return Product.objects.get(id=value, is_public=True)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError('Choose an existing public catalogue product.') from exc

    def validate_currency(self, value):
        return (value or default_currency()).strip().upper()

    @transaction.atomic
    def create(self, validated_data):
        SupplierProductOffer = apps.get_model('marketplace', 'SupplierProductOffer')
        supplier_profile = self.context['supplier_profile']
        user = self.context['request'].user
        product = validated_data.pop('product_id')

        offer, _ = SupplierProductOffer.objects.update_or_create(
            supplier=supplier_profile,
            product=product,
            defaults={
                'supplier_unit_cost': validated_data['supplier_unit_cost'],
                'currency': validated_data.get('currency') or default_currency(),
                'available_quantity': validated_data['available_quantity'],
                'lead_time_days': validated_data.get('lead_time_days') or 0,
                'supplier_sku': (validated_data.get('supplier_sku') or '').strip(),
                'notes': (validated_data.get('notes') or '').strip(),
                'status': SupplierProductOffer.STATUS_PENDING_REVIEW,
                'submitted_by': user,
                'reviewed_by': None,
                'reviewed_at': None,
                'review_note': '',
            },
        )
        if offer.stockrecord_id:
            offer.stockrecord.num_in_stock = 0
            offer.stockrecord.save(update_fields=['num_in_stock'])
        return offer

    def update(self, instance, validated_data):
        for field in ('supplier_unit_cost', 'available_quantity', 'lead_time_days'):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        if 'currency' in validated_data:
            instance.currency = validated_data['currency'] or default_currency()
        for field in ('supplier_sku', 'notes'):
            if field in validated_data:
                setattr(instance, field, (validated_data[field] or '').strip())
        instance.status = instance.STATUS_PENDING_REVIEW
        instance.reviewed_by = None
        instance.reviewed_at = None
        instance.review_note = ''
        instance.save()
        if instance.stockrecord_id:
            instance.stockrecord.num_in_stock = 0
            instance.stockrecord.save(update_fields=['num_in_stock'])
        return instance


class SupplierProductOfferModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected', 'changes_requested', 'suspended', 'pending_review'])
    review_note = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        status_value = attrs['status']
        review_note = (attrs.get('review_note') or '').strip()
        if status_value in {'rejected', 'changes_requested', 'suspended'} and not review_note:
            raise serializers.ValidationError({'review_note': 'A review note is required for this decision.'})
        attrs['review_note'] = review_note
        return attrs

    def update(self, instance, validated_data):
        return apply_supplier_offer_approval(
            instance,
            reviewer=self.context['request'].user,
            status_value=validated_data['status'],
            review_note=validated_data.get('review_note', ''),
        )


class SupplierProductOfferListSerializer(serializers.Serializer):
    def to_representation(self, offer):
        return _supplier_offer_payload(offer)


class SupplierProductRequestWriteSerializer(serializers.Serializer):
    requested_title = serializers.CharField(max_length=255)
    brand = serializers.CharField(required=False, allow_blank=True, max_length=128)
    category_hint = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    specs = serializers.JSONField(required=False)
    supplier_sku = serializers.CharField(required=False, allow_blank=True, max_length=128)
    supplier_unit_cost = serializers.DecimalField(required=False, allow_null=True, max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    currency = serializers.CharField(required=False, allow_blank=True, max_length=12)
    available_quantity = serializers.IntegerField(required=False, min_value=0, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        SupplierProductRequest = apps.get_model('marketplace', 'SupplierProductRequest')
        supplier_profile = self.context['supplier_profile']
        return SupplierProductRequest.objects.create(
            supplier=supplier_profile,
            submitted_by=self.context['request'].user,
            requested_title=validated_data['requested_title'].strip(),
            brand=(validated_data.get('brand') or '').strip(),
            category_hint=(validated_data.get('category_hint') or '').strip(),
            description=(validated_data.get('description') or '').strip(),
            specs=validated_data.get('specs') or {},
            supplier_sku=(validated_data.get('supplier_sku') or '').strip(),
            supplier_unit_cost=validated_data.get('supplier_unit_cost'),
            currency=(validated_data.get('currency') or default_currency()).strip().upper(),
            available_quantity=validated_data.get('available_quantity') or 0,
            notes=(validated_data.get('notes') or '').strip(),
        )


class SupplierProductRequestModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected', 'changes_requested', 'pending_review'])
    linked_product_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    review_note = serializers.CharField(required=False, allow_blank=True)

    def validate_linked_product_id(self, value):
        if value is None:
            return None
        Product = apps.get_model('catalogue', 'Product')
        try:
            return Product.objects.get(id=value)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError('Choose an existing catalogue product.') from exc

    def validate(self, attrs):
        status_value = attrs['status']
        review_note = (attrs.get('review_note') or '').strip()
        linked_product = attrs.get('linked_product_id')
        if status_value == 'approved' and linked_product is None:
            raise serializers.ValidationError({'linked_product_id': 'Link the approved request to a catalogue product.'})
        if status_value in {'rejected', 'changes_requested'} and not review_note:
            raise serializers.ValidationError({'review_note': 'A review note is required for this decision.'})
        attrs['review_note'] = review_note
        return attrs

    def update(self, instance, validated_data):
        linked_product = validated_data.pop('linked_product_id', serializers.empty)
        instance.status = validated_data['status']
        instance.review_note = validated_data.get('review_note', '')
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        if linked_product is not serializers.empty:
            instance.linked_product = linked_product
        instance.save(update_fields=['status', 'review_note', 'reviewed_by', 'reviewed_at', 'linked_product', 'updated_at'])
        return instance


class SupplierProductRequestListSerializer(serializers.Serializer):
    def to_representation(self, product_request):
        return _supplier_product_request_payload(product_request)


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
