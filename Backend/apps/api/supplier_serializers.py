from django.apps import apps
from django.db.models import Sum
from django.template.defaultfilters import slugify
from rest_framework import serializers

from apps.common.products import serialize_product_card

from .serializers import ProductWriteSerializer


class SupplierProfileSerializer(serializers.Serializer):
    def to_representation(self, supplier_profile):
        partner = supplier_profile.partner
        return {
            'id': supplier_profile.id,
            'status': supplier_profile.status,
            'company_name': supplier_profile.company_name,
            'contact_name': supplier_profile.contact_name,
            'phone': supplier_profile.phone,
            'country_code': supplier_profile.country_code,
            'website': supplier_profile.website,
            'notes': supplier_profile.notes,
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'code': partner.code,
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

    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.save(update_fields=['status'])
        return instance


class SupplierDashboardSerializer(serializers.Serializer):
    def to_representation(self, supplier_profile):
        Product = apps.get_model('catalogue', 'Product')
        StockRecord = apps.get_model('partner', 'StockRecord')
        partner = supplier_profile.partner

        stockrecords = StockRecord.objects.filter(partner=partner).select_related('product')
        product_ids = stockrecords.values_list('product_id', flat=True)
        products = Product.objects.filter(id__in=product_ids).exclude(structure='parent').distinct()

        return {
            'supplier': SupplierProfileSerializer(supplier_profile).data,
            'metrics': {
                'product_count': products.count(),
                'stockrecord_count': stockrecords.count(),
                'public_product_count': products.filter(is_public=True).count(),
                'low_stock_count': stockrecords.filter(num_in_stock__lte=5).count(),
                'inventory_units': stockrecords.aggregate(total=Sum('num_in_stock')).get('total') or 0,
            },
        }


class SupplierProductWriteSerializer(ProductWriteSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs.pop('partner_id', None)
        attrs.pop('partner_name', None)
        return attrs

    def _resolve_partner(self, product, payload):
        supplier_profile = self.context['supplier_profile']
        return supplier_profile.partner


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
        item['shared_catalog'] = product.stockrecords.exclude(partner=supplier_profile.partner).exists()
        return item
