from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from oscar.core.loading import get_model
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .checkout_utils import serialize_shipping_address
from .order_serializers import AdminOrderDetailSerializer, OrderLineSerializer, _order_note_payload
from apps.accounts.delivery_locations import clean_location_payload, upsert_shipping_address_location


def _decimal(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _bool_value(value, default=False) -> bool:
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


def _page(request, queryset, serializer, default_page_size=50):
    page = max(int(request.query_params.get('page', 1) or 1), 1)
    page_size = min(max(int(request.query_params.get('page_size', default_page_size) or default_page_size), 1), 200)
    total = queryset.count()
    start = (page - 1) * page_size
    rows = queryset[start : start + page_size]
    return {
        'results': [serializer(row) for row in rows],
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'num_pages': (total + page_size - 1) // page_size if page_size else 1,
            'has_next': start + page_size < total,
        },
    }


def _payload_fields(request, allowed):
    return {field: request.data[field] for field in allowed if field in request.data}


def _clean_blank(value):
    return None if value in ('', None) else value


def _clean_positive_int(value, field_name, *, required=False):
    value = _clean_blank(value)
    if value is None:
        if required:
            raise serializers.ValidationError({field_name: f'{field_name.replace("_", " ").title()} is required.'})
        return None
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError({field_name: 'Enter a valid whole number.'}) from exc
    if value <= 0:
        raise serializers.ValidationError({field_name: 'Enter a number greater than zero.'})
    return value


def _clean_nonnegative_int(value, field_name, *, required=False):
    value = _clean_blank(value)
    if value is None:
        if required:
            raise serializers.ValidationError({field_name: f'{field_name.replace("_", " ").title()} is required.'})
        return None
    try:
        value = int(value)
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError({field_name: 'Enter a valid whole number.'}) from exc
    if value < 0:
        raise serializers.ValidationError({field_name: 'Enter zero or a greater number.'})
    return value


def _clean_decimal_value(value, field_name, *, required=False):
    value = _clean_blank(value)
    if value is None:
        if required:
            raise serializers.ValidationError({field_name: f'{field_name.replace("_", " ").title()} is required.'})
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise serializers.ValidationError({field_name: 'Enter a valid number.'}) from exc


def _validate_choice(model, field_name, value, choices):
    valid_values = {choice_value for choice_value, _label in choices}
    if value not in valid_values:
        readable = ', '.join(str(choice_value) for choice_value in sorted(valid_values))
        raise serializers.ValidationError({field_name: f'Choose one of: {readable}.'})
    return value


def _clean_proxy_class(value):
    value = _clean_blank(value)
    if value is None:
        return None
    if '.' not in str(value):
        raise serializers.ValidationError(
            {'proxy_class': 'Enter a full Python import path, or leave proxy class empty.'}
        )
    return str(value)


def _validate_range(range_id):
    range_id = _clean_positive_int(range_id, 'range_id')
    if range_id is None:
        return None
    Range = get_model('offer', 'Range')
    if not Range.objects.filter(id=range_id).exists():
        raise serializers.ValidationError({'range_id': 'Select an existing product range.'})
    return range_id


def _validate_offer_relation(model_name, field_name, value):
    object_id = _clean_positive_int(value, field_name, required=True)
    model = get_model('offer', model_name)
    if not model.objects.filter(id=object_id).exists():
        raise serializers.ValidationError({field_name: f'Select an existing {model_name.lower()}.'})
    return object_id


def _validate_offer_status(Offer, status_value):
    allowed = {Offer.OPEN, Offer.SUSPENDED, Offer.CONSUMED}
    if status_value not in allowed:
        raise serializers.ValidationError({'status': f'Choose one of: {", ".join(sorted(allowed))}.'})
    return status_value


def _validate_offer_dates(start_datetime, end_datetime):
    if start_datetime and end_datetime and end_datetime <= start_datetime:
        raise serializers.ValidationError({'end_datetime': 'End date must be after the start date.'})


def _clean_offer(offer):
    try:
        offer.full_clean()
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages) from exc
    _validate_offer_dates(offer.start_datetime, offer.end_datetime)
    return offer


def _safe_offer_component_text(component, fallback):
    try:
        return str(component)
    except Exception:
        return fallback


class AdminDashboardSummaryAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Order = get_model('order', 'Order')
        Product = get_model('catalogue', 'Product')
        StockRecord = get_model('partner', 'StockRecord')
        User = get_user_model()

        pending_statuses = ['Pending', 'Processing', 'Packed']
        low_stock = StockRecord.objects.filter(num_in_stock__lte=F('low_stock_threshold'))
        recent_orders = Order.objects.order_by('-date_placed')[:8]

        return Response(
            {
                'summary': {
                    'revenue': _decimal(Order.objects.aggregate(total=Sum('total_incl_tax'))['total']),
                    'orders': Order.objects.count(),
                    'customers': User.objects.filter(is_staff=False).count(),
                    'products': Product.objects.count(),
                    'low_stock': low_stock.count(),
                    'pending_orders': Order.objects.filter(status__in=pending_statuses).count(),
                },
                'recent_activity': [
                    {
                        'type': 'order',
                        'id': order.id,
                        'label': order.number,
                        'status': order.status,
                        'total': _decimal(order.total_incl_tax),
                        'created_at': order.date_placed,
                    }
                    for order in recent_orders
                ],
            }
        )


def _category_payload(category):
    return {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description or '',
        'is_public': category.is_public,
        'parent_id': category.get_parent().id if category.get_parent() else None,
        'depth': category.depth,
        'numchild': category.numchild,
    }


class AdminCategoryCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Category = get_model('catalogue', 'Category')
        return Response(_page(request, Category.objects.order_by('path'), _category_payload))

    def post(self, request):
        Category = get_model('catalogue', 'Category')
        parent_id = request.data.get('parent_id')
        data = {
            'name': request.data.get('name', ''),
            'slug': request.data.get('slug') or slugify(request.data.get('name', '')),
            'description': request.data.get('description', ''),
            'is_public': bool(request.data.get('is_public', True)),
        }
        if parent_id:
            parent = get_object_or_404(Category, id=parent_id)
            category = parent.add_child(**data)
        else:
            category = Category.add_root(**data)
        return Response({'category': _category_payload(category)}, status=status.HTTP_201_CREATED)


class AdminCategoryDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, category_id: int):
        return Response({'category': _category_payload(get_object_or_404(get_model('catalogue', 'Category'), id=category_id))})

    def patch(self, request, category_id: int):
        category = get_object_or_404(get_model('catalogue', 'Category'), id=category_id)
        for field in ['name', 'slug', 'description', 'is_public']:
            if field in request.data:
                setattr(category, field, request.data[field])
        category.save()
        return Response({'category': _category_payload(category)})

    def delete(self, request, category_id: int):
        get_object_or_404(get_model('catalogue', 'Category'), id=category_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCategoryChildrenAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, category_id: int):
        parent = get_object_or_404(get_model('catalogue', 'Category'), id=category_id)
        category = parent.add_child(
            name=request.data.get('name', ''),
            slug=request.data.get('slug') or slugify(request.data.get('name', '')),
            description=request.data.get('description', ''),
            is_public=bool(request.data.get('is_public', True)),
        )
        return Response({'category': _category_payload(category)}, status=status.HTTP_201_CREATED)


def _product_class_payload(product_class):
    return {
        'id': product_class.id,
        'name': product_class.name,
        'slug': product_class.slug,
        'requires_shipping': product_class.requires_shipping,
        'track_stock': product_class.track_stock,
    }


class AdminProductTypeCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        ProductClass = get_model('catalogue', 'ProductClass')
        return Response(_page(request, ProductClass.objects.order_by('name'), _product_class_payload))

    def post(self, request):
        ProductClass = get_model('catalogue', 'ProductClass')
        product_class = ProductClass.objects.create(
            name=request.data.get('name', ''),
            slug=request.data.get('slug') or slugify(request.data.get('name', '')),
            requires_shipping=bool(request.data.get('requires_shipping', True)),
            track_stock=bool(request.data.get('track_stock', True)),
        )
        return Response({'product_type': _product_class_payload(product_class)}, status=status.HTTP_201_CREATED)


class AdminProductTypeDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, product_type_id: int):
        return Response({'product_type': _product_class_payload(get_object_or_404(get_model('catalogue', 'ProductClass'), id=product_type_id))})

    def patch(self, request, product_type_id: int):
        product_class = get_object_or_404(get_model('catalogue', 'ProductClass'), id=product_type_id)
        for field in ['name', 'slug', 'requires_shipping', 'track_stock']:
            if field in request.data:
                setattr(product_class, field, request.data[field])
        product_class.save()
        return Response({'product_type': _product_class_payload(product_class)})

    def delete(self, request, product_type_id: int):
        get_object_or_404(get_model('catalogue', 'ProductClass'), id=product_type_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _attribute_payload(attribute):
    return {
        'id': attribute.id,
        'product_class_id': attribute.product_class_id,
        'name': attribute.name,
        'code': attribute.code,
        'type': attribute.type,
        'required': attribute.required,
        'option_group_id': attribute.option_group_id,
    }


class AdminAttributeCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        ProductAttribute = get_model('catalogue', 'ProductAttribute')
        return Response(_page(request, ProductAttribute.objects.select_related('product_class').order_by('code'), _attribute_payload))

    def post(self, request):
        ProductAttribute = get_model('catalogue', 'ProductAttribute')
        ProductClass = get_model('catalogue', 'ProductClass')
        attribute = ProductAttribute.objects.create(
            product_class=get_object_or_404(ProductClass, id=request.data.get('product_class_id')),
            name=request.data.get('name', ''),
            code=request.data.get('code') or slugify(request.data.get('name', '')).replace('-', '_'),
            type=request.data.get('type', 'text'),
            required=bool(request.data.get('required', False)),
        )
        return Response({'attribute': _attribute_payload(attribute)}, status=status.HTTP_201_CREATED)


class AdminAttributeDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, attribute_id: int):
        return Response({'attribute': _attribute_payload(get_object_or_404(get_model('catalogue', 'ProductAttribute'), id=attribute_id))})

    def patch(self, request, attribute_id: int):
        attribute = get_object_or_404(get_model('catalogue', 'ProductAttribute'), id=attribute_id)
        for field in ['name', 'code', 'type', 'required']:
            if field in request.data:
                setattr(attribute, field, request.data[field])
        attribute.save()
        return Response({'attribute': _attribute_payload(attribute)})

    def delete(self, request, attribute_id: int):
        get_object_or_404(get_model('catalogue', 'ProductAttribute'), id=attribute_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _option_payload(option):
    return {
        'id': option.id,
        'name': option.name,
        'code': option.code,
        'type': option.type,
        'required': option.required,
        'help_text': option.help_text,
        'order': option.order,
    }


class AdminOptionCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Option = get_model('catalogue', 'Option')
        return Response(_page(request, Option.objects.order_by('order', 'name'), _option_payload))

    def post(self, request):
        Option = get_model('catalogue', 'Option')
        option = Option.objects.create(
            name=request.data.get('name', ''),
            code=request.data.get('code') or slugify(request.data.get('name', '')).replace('-', '_'),
            type=request.data.get('type', 'text'),
            required=bool(request.data.get('required', False)),
            help_text=request.data.get('help_text', ''),
            order=request.data.get('order') or 0,
        )
        return Response({'option': _option_payload(option)}, status=status.HTTP_201_CREATED)


class AdminOptionDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, option_id: int):
        return Response({'option': _option_payload(get_object_or_404(get_model('catalogue', 'Option'), id=option_id))})

    def patch(self, request, option_id: int):
        option = get_object_or_404(get_model('catalogue', 'Option'), id=option_id)
        for field in ['name', 'code', 'type', 'required', 'help_text', 'order']:
            if field in request.data:
                setattr(option, field, request.data[field])
        option.save()
        return Response({'option': _option_payload(option)})

    def delete(self, request, option_id: int):
        get_object_or_404(get_model('catalogue', 'Option'), id=option_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _stock_alert_payload(alert):
    return {
        'id': alert.id,
        'status': alert.status,
        'threshold': alert.threshold,
        'date_created': alert.date_created,
        'date_closed': alert.date_closed,
        'stockrecord': {
            'id': alert.stockrecord_id,
            'partner_sku': alert.stockrecord.partner_sku,
            'num_in_stock': alert.stockrecord.num_in_stock,
            'product_id': alert.stockrecord.product_id,
            'product_title': alert.stockrecord.product.title if alert.stockrecord.product else '',
        },
    }


class AdminStockAlertCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        StockAlert = get_model('partner', 'StockAlert')
        return Response(_page(request, StockAlert.objects.select_related('stockrecord__product').order_by('-date_created'), _stock_alert_payload))


class AdminStockAlertDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, alert_id: int):
        alert = get_object_or_404(get_model('partner', 'StockAlert'), id=alert_id)
        if 'status' in request.data:
            alert.status = request.data['status']
            if str(alert.status).lower() == 'closed':
                alert.date_closed = timezone.now()
            alert.save(update_fields=['status', 'date_closed'])
        return Response({'stock_alert': _stock_alert_payload(alert)})


class AdminLowStockAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        StockRecord = get_model('partner', 'StockRecord')
        rows = StockRecord.objects.select_related('product', 'partner').filter(num_in_stock__lte=F('low_stock_threshold')).order_by('num_in_stock')
        return Response(
            _page(
                request,
                rows,
                lambda row: {
                    'stockrecord_id': row.id,
                    'product_id': row.product_id,
                    'product_title': row.product.title if row.product else '',
                    'partner_id': row.partner_id,
                    'partner_name': row.partner.name if row.partner else '',
                    'partner_sku': row.partner_sku,
                    'num_in_stock': row.num_in_stock,
                    'low_stock_threshold': row.low_stock_threshold,
                },
            )
        )


def _voucher_payload(voucher):
    return {
        'id': voucher.id,
        'name': voucher.name,
        'code': voucher.code,
        'usage': voucher.usage,
        'start_datetime': voucher.start_datetime,
        'end_datetime': voucher.end_datetime,
        'num_basket_additions': voucher.num_basket_additions,
        'num_orders': voucher.num_orders,
        'total_discount': _decimal(voucher.total_discount),
        'date_created': voucher.date_created,
        'offers': [_offer_payload(offer) for offer in voucher.offers.select_related('condition', 'benefit').all()],
    }


class AdminVoucherCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Voucher = get_model('voucher', 'Voucher')
        return Response(_page(request, Voucher.objects.order_by('-date_created'), _voucher_payload))

    def post(self, request):
        Voucher = get_model('voucher', 'Voucher')
        voucher = Voucher.objects.create(
            name=request.data.get('name', ''),
            code=request.data.get('code', ''),
            usage=request.data.get('usage', 'Single use'),
            start_datetime=request.data.get('start_datetime') or timezone.now(),
            end_datetime=request.data.get('end_datetime') or timezone.now(),
        )
        return Response({'voucher': _voucher_payload(voucher)}, status=status.HTTP_201_CREATED)


class AdminVoucherDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, voucher_id: int):
        return Response({'voucher': _voucher_payload(get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id))})

    def patch(self, request, voucher_id: int):
        voucher = get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id)
        for field in ['name', 'code', 'usage', 'start_datetime', 'end_datetime']:
            if field in request.data:
                setattr(voucher, field, request.data[field])
        voucher.save()
        return Response({'voucher': _voucher_payload(voucher)})

    def delete(self, request, voucher_id: int):
        get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminVoucherStatsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, voucher_id: int):
        voucher = get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id)
        return Response({'stats': _voucher_payload(voucher)})


class AdminVoucherOfferCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, voucher_id: int):
        voucher = get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id)
        return Response({'results': [_offer_payload(offer) for offer in voucher.offers.select_related('condition', 'benefit').all()]})

    def post(self, request, voucher_id: int):
        voucher = get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id)
        offer = get_object_or_404(get_model('offer', 'ConditionalOffer'), id=request.data.get('offer_id'))
        if offer.offer_type != offer.VOUCHER:
            offer.offer_type = offer.VOUCHER
            offer.save(update_fields=['offer_type'])
        voucher.offers.add(offer)
        return Response({'voucher': _voucher_payload(voucher)}, status=status.HTTP_201_CREATED)

    def delete(self, request, voucher_id: int):
        voucher = get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id)
        offer = get_object_or_404(get_model('offer', 'ConditionalOffer'), id=request.data.get('offer_id'))
        voucher.offers.remove(offer)
        return Response({'voucher': _voucher_payload(voucher)})


def _offer_payload(offer):
    return {
        'id': offer.id,
        'name': offer.name,
        'slug': offer.slug,
        'description': offer.description,
        'offer_type': offer.offer_type,
        'exclusive': offer.exclusive,
        'status': offer.status,
        'priority': offer.priority,
        'start_datetime': offer.start_datetime,
        'end_datetime': offer.end_datetime,
        'num_applications': offer.num_applications,
        'num_orders': offer.num_orders,
        'total_discount': _decimal(offer.total_discount),
        'condition_id': offer.condition_id,
        'benefit_id': offer.benefit_id,
        'condition': _condition_payload(offer.condition) if getattr(offer, 'condition_id', None) else None,
        'benefit': _benefit_payload(offer.benefit) if getattr(offer, 'benefit_id', None) else None,
        'voucher_ids': list(offer.vouchers.values_list('id', flat=True)) if hasattr(offer, 'vouchers') else [],
    }


def _condition_payload(condition):
    fallback_name = f'{condition.type} condition'
    return {
        'id': condition.id,
        'type': condition.type,
        'range_id': condition.range_id,
        'range_name': condition.range.name if condition.range_id else '',
        'value': _decimal(condition.value),
        'proxy_class': condition.proxy_class or '',
        'name': _safe_offer_component_text(condition, fallback_name),
        'description': _safe_offer_component_text(condition, fallback_name),
    }


def _benefit_payload(benefit):
    fallback_name = f'{benefit.type} benefit'
    return {
        'id': benefit.id,
        'type': benefit.type,
        'range_id': benefit.range_id,
        'range_name': benefit.range.name if benefit.range_id else '',
        'value': _decimal(benefit.value),
        'max_affected_items': benefit.max_affected_items,
        'proxy_class': benefit.proxy_class or '',
        'name': _safe_offer_component_text(benefit, fallback_name),
        'description': _safe_offer_component_text(benefit, fallback_name),
    }


def _save_offer_component(instance, data, allowed_fields):
    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field == 'range_id':
                value = _validate_range(value)
            elif field == 'value':
                value = _clean_decimal_value(value, field)
            elif field == 'max_affected_items':
                value = _clean_positive_int(value, field)
            elif field == 'proxy_class':
                value = _clean_proxy_class(value)
            setattr(instance, field, value)
    try:
        instance.full_clean()
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message_dict if hasattr(exc, 'message_dict') else exc.messages) from exc
    instance.save()
    return instance


class AdminOfferConditionCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Condition = get_model('offer', 'Condition')
        return Response(_page(request, Condition.objects.select_related('range').order_by('id'), _condition_payload))

    def post(self, request):
        Condition = get_model('offer', 'Condition')
        condition_type = request.data.get('type', Condition.COUNT)
        _validate_choice(Condition, 'type', condition_type, Condition.TYPE_CHOICES)
        condition = Condition(
            type=condition_type,
            range_id=_validate_range(request.data.get('range_id')),
            value=_clean_decimal_value(request.data.get('value'), 'value'),
            proxy_class=_clean_proxy_class(request.data.get('proxy_class')),
        )
        _save_offer_component(condition, {}, [])
        return Response({'condition': _condition_payload(condition)}, status=status.HTTP_201_CREATED)


class AdminOfferConditionDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, condition_id: int):
        return Response({'condition': _condition_payload(get_object_or_404(get_model('offer', 'Condition'), id=condition_id))})

    def patch(self, request, condition_id: int):
        condition = get_object_or_404(get_model('offer', 'Condition'), id=condition_id)
        if 'type' in request.data:
            _validate_choice(type(condition), 'type', request.data.get('type'), type(condition).TYPE_CHOICES)
        _save_offer_component(condition, request.data, ['type', 'range_id', 'value', 'proxy_class'])
        return Response({'condition': _condition_payload(condition)})

    def delete(self, request, condition_id: int):
        get_object_or_404(get_model('offer', 'Condition'), id=condition_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminOfferBenefitCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Benefit = get_model('offer', 'Benefit')
        return Response(_page(request, Benefit.objects.select_related('range').order_by('id'), _benefit_payload))

    def post(self, request):
        Benefit = get_model('offer', 'Benefit')
        benefit_type = request.data.get('type', Benefit.PERCENTAGE)
        _validate_choice(Benefit, 'type', benefit_type, Benefit.TYPE_CHOICES)
        benefit = Benefit(
            type=benefit_type,
            range_id=_validate_range(request.data.get('range_id')),
            value=_clean_decimal_value(request.data.get('value'), 'value'),
            max_affected_items=_clean_positive_int(request.data.get('max_affected_items'), 'max_affected_items'),
            proxy_class=_clean_proxy_class(request.data.get('proxy_class')),
        )
        _save_offer_component(benefit, {}, [])
        return Response({'benefit': _benefit_payload(benefit)}, status=status.HTTP_201_CREATED)


class AdminOfferBenefitDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, benefit_id: int):
        return Response({'benefit': _benefit_payload(get_object_or_404(get_model('offer', 'Benefit'), id=benefit_id))})

    def patch(self, request, benefit_id: int):
        benefit = get_object_or_404(get_model('offer', 'Benefit'), id=benefit_id)
        if 'type' in request.data:
            _validate_choice(type(benefit), 'type', request.data.get('type'), type(benefit).TYPE_CHOICES)
        _save_offer_component(benefit, request.data, ['type', 'range_id', 'value', 'max_affected_items', 'proxy_class'])
        return Response({'benefit': _benefit_payload(benefit)})

    def delete(self, request, benefit_id: int):
        get_object_or_404(get_model('offer', 'Benefit'), id=benefit_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminOfferMetadataAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Offer = get_model('offer', 'ConditionalOffer')
        Condition = get_model('offer', 'Condition')
        Benefit = get_model('offer', 'Benefit')
        return Response(
            {
                'offer_types': [{'value': value, 'label': str(label)} for value, label in Offer.TYPE_CHOICES],
                'offer_statuses': [
                    {'value': Offer.OPEN, 'label': 'Open'},
                    {'value': Offer.SUSPENDED, 'label': 'Suspended'},
                    {'value': Offer.CONSUMED, 'label': 'Consumed'},
                ],
                'condition_types': [{'value': value, 'label': str(label)} for value, label in Condition.TYPE_CHOICES],
                'benefit_types': [{'value': value, 'label': str(label)} for value, label in Benefit.TYPE_CHOICES],
            }
        )


class AdminOfferCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Offer = get_model('offer', 'ConditionalOffer')
        return Response(_page(request, Offer.objects.order_by('priority', 'name'), _offer_payload))

    def post(self, request):
        Offer = get_model('offer', 'ConditionalOffer')
        condition_id = _validate_offer_relation('Condition', 'condition_id', request.data.get('condition_id'))
        benefit_id = _validate_offer_relation('Benefit', 'benefit_id', request.data.get('benefit_id'))
        voucher_id = request.data.get('voucher_id')
        name = (request.data.get('name') or '').strip()
        if not name:
            raise serializers.ValidationError({'name': 'Offer name is required.'})
        offer_type = request.data.get('offer_type') or (Offer.VOUCHER if voucher_id else Offer.SITE)
        _validate_choice(Offer, 'offer_type', offer_type, Offer.TYPE_CHOICES)
        status_value = _validate_offer_status(Offer, request.data.get('status', Offer.OPEN))
        offer = Offer(
            name=request.data.get('name', ''),
            slug=request.data.get('slug') or slugify(name),
            description=request.data.get('description', ''),
            offer_type=offer_type,
            status=status_value,
            exclusive=bool(request.data.get('exclusive', False)),
            condition_id=condition_id,
            benefit_id=benefit_id,
            priority=_clean_nonnegative_int(request.data.get('priority'), 'priority') or 0,
            start_datetime=request.data.get('start_datetime') or None,
            end_datetime=request.data.get('end_datetime') or None,
        )
        _clean_offer(offer)
        offer.save()
        if voucher_id:
            voucher = get_object_or_404(get_model('voucher', 'Voucher'), id=voucher_id)
            voucher.offers.add(offer)
        return Response({'offer': _offer_payload(offer)}, status=status.HTTP_201_CREATED)


class AdminOfferDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, offer_id: int):
        return Response({'offer': _offer_payload(get_object_or_404(get_model('offer', 'ConditionalOffer'), id=offer_id))})

    def patch(self, request, offer_id: int):
        Offer = get_model('offer', 'ConditionalOffer')
        offer = get_object_or_404(get_model('offer', 'ConditionalOffer'), id=offer_id)
        for field in ['name', 'slug', 'description', 'offer_type', 'exclusive', 'status', 'priority', 'start_datetime', 'end_datetime', 'condition_id', 'benefit_id']:
            if field in request.data:
                value = request.data[field]
                if field == 'name':
                    value = (value or '').strip()
                    if not value:
                        raise serializers.ValidationError({'name': 'Offer name is required.'})
                elif field == 'offer_type':
                    value = _validate_choice(Offer, 'offer_type', value, Offer.TYPE_CHOICES)
                elif field == 'status':
                    value = _validate_offer_status(Offer, value)
                elif field == 'priority':
                    value = _clean_nonnegative_int(value, 'priority') or 0
                elif field == 'condition_id':
                    value = _validate_offer_relation('Condition', 'condition_id', value)
                elif field == 'benefit_id':
                    value = _validate_offer_relation('Benefit', 'benefit_id', value)
                elif field in {'start_datetime', 'end_datetime'} and value in ('', None):
                    value = None
                setattr(offer, field, value)
        _clean_offer(offer)
        offer.save()
        return Response({'offer': _offer_payload(offer)})

    def delete(self, request, offer_id: int):
        get_object_or_404(get_model('offer', 'ConditionalOffer'), id=offer_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminOfferStatusAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, offer_id: int):
        Offer = get_model('offer', 'ConditionalOffer')
        offer = get_object_or_404(Offer, id=offer_id)
        offer.status = _validate_offer_status(Offer, request.data.get('status', offer.status))
        offer.save(update_fields=['status'])
        return Response({'offer': _offer_payload(offer)})


def _range_payload(range_obj):
    return {
        'id': range_obj.id,
        'name': range_obj.name,
        'slug': range_obj.slug,
        'description': range_obj.description,
        'is_public': range_obj.is_public,
        'includes_all_products': range_obj.includes_all_products,
        'num_products': range_obj.num_products(),
    }


class AdminRangeCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Range = get_model('offer', 'Range')
        return Response(_page(request, Range.objects.order_by('name'), _range_payload))

    def post(self, request):
        Range = get_model('offer', 'Range')
        range_obj = Range.objects.create(
            name=request.data.get('name', ''),
            slug=request.data.get('slug') or slugify(request.data.get('name', '')),
            description=request.data.get('description', ''),
            is_public=bool(request.data.get('is_public', True)),
            includes_all_products=bool(request.data.get('includes_all_products', False)),
        )
        return Response({'range': _range_payload(range_obj)}, status=status.HTTP_201_CREATED)


class AdminRangeDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, range_id: int):
        return Response({'range': _range_payload(get_object_or_404(get_model('offer', 'Range'), id=range_id))})

    def patch(self, request, range_id: int):
        range_obj = get_object_or_404(get_model('offer', 'Range'), id=range_id)
        for field in ['name', 'slug', 'description', 'is_public', 'includes_all_products']:
            if field in request.data:
                setattr(range_obj, field, request.data[field])
        range_obj.save()
        return Response({'range': _range_payload(range_obj)})

    def delete(self, request, range_id: int):
        get_object_or_404(get_model('offer', 'Range'), id=range_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminRangeProductAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, range_id: int):
        range_obj = get_object_or_404(get_model('offer', 'Range'), id=range_id)
        products = range_obj.all_products().order_by('title')[:200]
        return Response({'results': [{'id': product.id, 'title': product.title, 'upc': product.upc} for product in products]})

    def post(self, request, range_id: int):
        range_obj = get_object_or_404(get_model('offer', 'Range'), id=range_id)
        product = get_object_or_404(get_model('catalogue', 'Product'), id=request.data.get('product_id'))
        range_obj.add_product(product)
        return Response({'range': _range_payload(range_obj)}, status=status.HTTP_201_CREATED)

    def delete(self, request, range_id: int):
        range_obj = get_object_or_404(get_model('offer', 'Range'), id=range_id)
        product = get_object_or_404(get_model('catalogue', 'Product'), id=request.data.get('product_id'))
        range_obj.remove_product(product)
        return Response({'range': _range_payload(range_obj)})


def _review_payload(review):
    return {
        'id': review.id,
        'product_id': review.product_id,
        'product_title': review.product.title if review.product else '',
        'score': review.score,
        'title': review.title,
        'body': review.body,
        'user_id': review.user_id,
        'name': review.name,
        'email': review.email,
        'status': review.status,
        'date_created': review.date_created,
    }


class AdminReviewCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Review = get_model('reviews', 'ProductReview')
        return Response(_page(request, Review.objects.select_related('product', 'user').order_by('-date_created'), _review_payload))


class AdminReviewDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, review_id: int):
        return Response({'review': _review_payload(get_object_or_404(get_model('reviews', 'ProductReview'), id=review_id))})

    def patch(self, request, review_id: int):
        review = get_object_or_404(get_model('reviews', 'ProductReview'), id=review_id)
        for field in ['status', 'title', 'body', 'score']:
            if field in request.data:
                setattr(review, field, request.data[field])
        review.save()
        return Response({'review': _review_payload(review)})

    def delete(self, request, review_id: int):
        get_object_or_404(get_model('reviews', 'ProductReview'), id=review_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminOrderStatisticsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Order = get_model('order', 'Order')
        return Response(
            {
                'statistics': {
                    'orders': Order.objects.count(),
                    'revenue': _decimal(Order.objects.aggregate(total=Sum('total_incl_tax'))['total']),
                    'by_status': list(Order.objects.values('status').annotate(count=Count('id')).order_by('status')),
                }
            }
        )


class AdminOrderLineDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, order_number: str, line_id: int):
        Line = get_model('order', 'Line')
        line = get_object_or_404(Line.objects.select_related('order', 'product'), id=line_id, order__number=order_number)
        return Response({'line': OrderLineSerializer(line).data})


class AdminOrderShippingAddressAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, order_number: str):
        order = get_object_or_404(get_model('order', 'Order'), number=order_number)
        address = order.shipping_address
        if address is None:
            ShippingAddress = get_model('order', 'ShippingAddress')
            address = ShippingAddress()
            order.shipping_address = address
        for field in ['first_name', 'last_name', 'line1', 'line2', 'line3', 'line4', 'state', 'postcode', 'phone_number', 'notes']:
            if field in request.data:
                setattr(address, field, request.data[field])
        if 'country_code' in request.data:
            country_code = str(request.data.get('country_code') or '').strip().upper()
            if country_code:
                Country = apps.get_model('address', 'Country')
                country = Country.objects.filter(iso_3166_1_a2__iexact=country_code, is_shipping_country=True).first()
                if not country:
                    return Response({'error': {'detail': 'Unsupported shipping country.', 'errors': {'country_code': ['Unsupported shipping country.']}}}, status=status.HTTP_400_BAD_REQUEST)
                address.country = country
        address.save()
        location = clean_location_payload({
            'latitude': request.data.get('latitude'),
            'longitude': request.data.get('longitude'),
            'label': request.data.get('location_label', ''),
            'source': 'admin',
        })
        if location:
            upsert_shipping_address_location(address, location)
        order.shipping_address = address
        order.save(update_fields=['shipping_address'])
        return Response({'shipping_address': serialize_shipping_address(address)})


class AdminOrderNoteAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, order_number: str):
        order = get_object_or_404(get_model('order', 'Order'), number=order_number)
        return Response({'results': [_order_note_payload(note) for note in order.notes.select_related('user').all()]})

    def post(self, request, order_number: str):
        order = get_object_or_404(get_model('order', 'Order'), number=order_number)
        message = str(request.data.get('message', '') or '').strip()
        if not message:
            return Response({'error': {'detail': 'Message is required.', 'errors': {'message': ['This field is required.']}}}, status=status.HTTP_400_BAD_REQUEST)
        Note = get_model('order', 'OrderNote')
        note = Note.objects.create(order=order, user=request.user, message=message, note_type=request.data.get('note_type', 'Admin'))
        return Response({'note': _order_note_payload(note)}, status=status.HTTP_201_CREATED)


def _partner_payload(partner):
    return {'id': partner.id, 'code': partner.code, 'name': partner.name, 'user_count': partner.users.count()}


class AdminPartnerCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        Partner = get_model('partner', 'Partner')
        return Response(_page(request, Partner.objects.order_by('name'), _partner_payload))

    def post(self, request):
        Partner = get_model('partner', 'Partner')
        partner = Partner.objects.create(name=request.data.get('name', ''), code=request.data.get('code') or slugify(request.data.get('name', '')))
        return Response({'partner': _partner_payload(partner)}, status=status.HTTP_201_CREATED)


class AdminPartnerDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, partner_id: int):
        return Response({'partner': _partner_payload(get_object_or_404(get_model('partner', 'Partner'), id=partner_id))})

    def patch(self, request, partner_id: int):
        partner = get_object_or_404(get_model('partner', 'Partner'), id=partner_id)
        for field in ['name', 'code']:
            if field in request.data:
                setattr(partner, field, request.data[field])
        partner.save()
        return Response({'partner': _partner_payload(partner)})

    def delete(self, request, partner_id: int):
        get_object_or_404(get_model('partner', 'Partner'), id=partner_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminPartnerUserCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, partner_id: int):
        partner = get_object_or_404(get_model('partner', 'Partner'), id=partner_id)
        return Response({'results': [{'id': user.id, 'email': user.email, 'username': user.username} for user in partner.users.all()]})

    def post(self, request, partner_id: int):
        partner = get_object_or_404(get_model('partner', 'Partner'), id=partner_id)
        user = get_object_or_404(get_user_model(), id=request.data.get('user_id'))
        partner.users.add(user)
        return Response({'partner': _partner_payload(partner)}, status=status.HTTP_201_CREATED)


class AdminPartnerUserLinkAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, partner_id: int, user_id: int):
        partner = get_object_or_404(get_model('partner', 'Partner'), id=partner_id)
        partner.users.add(get_object_or_404(get_user_model(), id=user_id))
        return Response({'partner': _partner_payload(partner)})

    def delete(self, request, partner_id: int, user_id: int):
        partner = get_object_or_404(get_model('partner', 'Partner'), id=partner_id)
        partner.users.remove(get_object_or_404(get_user_model(), id=user_id))
        return Response({'partner': _partner_payload(partner)})


def _weight_based_payload(method):
    return {
        'id': method.id,
        'code': method.code,
        'name': method.name,
        'description': method.description,
        'default_weight': _decimal(method.default_weight),
        'bands': [{'id': band.id, 'upper_limit': _decimal(band.upper_limit), 'charge': _decimal(band.charge)} for band in method.bands.all()],
    }


def _distance_delivery_payload(method):
    return {
        'id': method.id,
        'code': method.code,
        'name': method.name,
        'description': method.description,
        'vehicle_type': method.vehicle_type,
        'base_fee': _decimal(method.base_fee),
        'rate_per_km': _decimal(method.rate_per_km),
        'minimum_fee': _decimal(method.minimum_fee),
        'maximum_distance_km': _decimal(method.maximum_distance_km) if method.maximum_distance_km is not None else None,
        'maximum_weight_kg': _decimal(method.maximum_weight_kg) if method.maximum_weight_kg is not None else None,
        'origin_label': method.origin_label,
        'origin_latitude': _decimal(method.origin_latitude),
        'origin_longitude': _decimal(method.origin_longitude),
        'is_active': method.is_active,
        'sort_order': method.sort_order,
    }


class AdminDistanceDeliveryMethodCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        DistanceDeliveryMethod = apps.get_model('accounts', 'DistanceDeliveryMethod')
        queryset = DistanceDeliveryMethod.objects.order_by('sort_order', 'name')
        return Response(_page(request, queryset, _distance_delivery_payload))

    def post(self, request):
        DistanceDeliveryMethod = apps.get_model('accounts', 'DistanceDeliveryMethod')
        name = (request.data.get('name') or '').strip()
        if not name:
            raise serializers.ValidationError({'name': 'Name is required.'})
        method = DistanceDeliveryMethod.objects.create(
            code=request.data.get('code') or slugify(name),
            name=name,
            description=request.data.get('description', ''),
            vehicle_type=request.data.get('vehicle_type') or DistanceDeliveryMethod.VEHICLE_MOTORCYCLE,
            base_fee=request.data.get('base_fee') or 0,
            rate_per_km=request.data.get('rate_per_km') or 0,
            minimum_fee=request.data.get('minimum_fee') or 0,
            maximum_distance_km=request.data.get('maximum_distance_km') or None,
            maximum_weight_kg=request.data.get('maximum_weight_kg') or None,
            origin_label=request.data.get('origin_label', ''),
            origin_latitude=request.data.get('origin_latitude'),
            origin_longitude=request.data.get('origin_longitude'),
            is_active=_bool_value(request.data.get('is_active'), default=True),
            sort_order=request.data.get('sort_order') or 0,
        )
        return Response({'method': _distance_delivery_payload(method)}, status=status.HTTP_201_CREATED)


class AdminDistanceDeliveryMethodDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, method_id: int):
        method = get_object_or_404(apps.get_model('accounts', 'DistanceDeliveryMethod'), id=method_id)
        return Response({'method': _distance_delivery_payload(method)})

    def patch(self, request, method_id: int):
        method = get_object_or_404(apps.get_model('accounts', 'DistanceDeliveryMethod'), id=method_id)
        for field in [
            'code',
            'name',
            'description',
            'vehicle_type',
            'base_fee',
            'rate_per_km',
            'minimum_fee',
            'maximum_distance_km',
            'maximum_weight_kg',
            'origin_label',
            'origin_latitude',
            'origin_longitude',
            'is_active',
            'sort_order',
        ]:
            if field in request.data:
                value = request.data[field]
                if field in {'maximum_distance_km', 'maximum_weight_kg'} and value in ('', None):
                    value = None
                if field == 'is_active':
                    value = _bool_value(value, default=method.is_active)
                setattr(method, field, value)
        method.save()
        return Response({'method': _distance_delivery_payload(method)})

    def delete(self, request, method_id: int):
        get_object_or_404(apps.get_model('accounts', 'DistanceDeliveryMethod'), id=method_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminWeightBasedShippingCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        WeightBased = get_model('shipping', 'WeightBased')
        return Response(_page(request, WeightBased.objects.prefetch_related('bands').order_by('name'), _weight_based_payload))

    def post(self, request):
        WeightBased = get_model('shipping', 'WeightBased')
        method = WeightBased.objects.create(
            code=request.data.get('code') or slugify(request.data.get('name', '')),
            name=request.data.get('name', ''),
            description=request.data.get('description', ''),
            default_weight=request.data.get('default_weight') or 0,
        )
        return Response({'method': _weight_based_payload(method)}, status=status.HTTP_201_CREATED)


class AdminWeightBasedShippingDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, method_id: int):
        return Response({'method': _weight_based_payload(get_object_or_404(get_model('shipping', 'WeightBased'), id=method_id))})

    def patch(self, request, method_id: int):
        method = get_object_or_404(get_model('shipping', 'WeightBased'), id=method_id)
        for field in ['code', 'name', 'description', 'default_weight']:
            if field in request.data:
                setattr(method, field, request.data[field])
        method.save()
        return Response({'method': _weight_based_payload(method)})

    def delete(self, request, method_id: int):
        get_object_or_404(get_model('shipping', 'WeightBased'), id=method_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminWeightBandCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, method_id: int):
        method = get_object_or_404(get_model('shipping', 'WeightBased'), id=method_id)
        if request.data.get('upper_limit') in (None, ''):
            raise serializers.ValidationError({'upper_limit': 'Upper limit is required.'})
        if request.data.get('charge') in (None, ''):
            raise serializers.ValidationError({'charge': 'Charge is required.'})
        band = method.bands.create(upper_limit=request.data.get('upper_limit'), charge=request.data.get('charge'))
        return Response({'band': {'id': band.id, 'upper_limit': _decimal(band.upper_limit), 'charge': _decimal(band.charge)}}, status=status.HTTP_201_CREATED)


class AdminWeightBandDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, method_id: int, band_id: int):
        band = get_object_or_404(get_model('shipping', 'WeightBand'), id=band_id, method_id=method_id)
        for field in ['upper_limit', 'charge']:
            if field in request.data:
                setattr(band, field, request.data[field])
        band.save()
        return Response({'band': {'id': band.id, 'upper_limit': _decimal(band.upper_limit), 'charge': _decimal(band.charge)}})

    def delete(self, request, method_id: int, band_id: int):
        get_object_or_404(get_model('shipping', 'WeightBand'), id=band_id, method_id=method_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _page_payload(page):
    return {'id': page.id, 'url': page.url, 'title': page.title, 'content': page.content, 'registration_required': page.registration_required}


class AdminPageCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        FlatPage = apps.get_model('flatpages', 'FlatPage')
        return Response(_page(request, FlatPage.objects.order_by('url'), _page_payload))

    def post(self, request):
        FlatPage = apps.get_model('flatpages', 'FlatPage')
        page = FlatPage.objects.create(
            url=request.data.get('url', ''),
            title=request.data.get('title', ''),
            content=request.data.get('content', ''),
            registration_required=bool(request.data.get('registration_required', False)),
        )
        page.sites.add(Site.objects.get_current())
        return Response({'page': _page_payload(page)}, status=status.HTTP_201_CREATED)


class AdminPageDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, page_id: int):
        return Response({'page': _page_payload(get_object_or_404(apps.get_model('flatpages', 'FlatPage'), id=page_id))})

    def patch(self, request, page_id: int):
        page = get_object_or_404(apps.get_model('flatpages', 'FlatPage'), id=page_id)
        for field in ['url', 'title', 'content', 'registration_required']:
            if field in request.data:
                setattr(page, field, request.data[field])
        page.save()
        return Response({'page': _page_payload(page)})

    def delete(self, request, page_id: int):
        get_object_or_404(apps.get_model('flatpages', 'FlatPage'), id=page_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _communication_payload(template):
    return {
        'id': template.id,
        'code': template.code,
        'name': template.name,
        'category': template.category,
        'email_subject_template': template.email_subject_template,
        'email_body_template': template.email_body_template,
        'email_body_html_template': template.email_body_html_template,
        'sms_template': template.sms_template,
    }


class AdminCommunicationCollectionAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from apps.notifications.templates import ensure_custom_communication_templates

        ensure_custom_communication_templates()
        CommunicationEventType = get_model('communication', 'CommunicationEventType')
        return Response({'results': [_communication_payload(row) for row in CommunicationEventType.objects.order_by('category', 'code')]})


class AdminCommunicationDetailAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, slug: str):
        from apps.notifications.templates import ensure_custom_communication_templates

        ensure_custom_communication_templates()
        template = get_object_or_404(get_model('communication', 'CommunicationEventType'), code=slug)
        return Response({'communication': _communication_payload(template)})

    def patch(self, request, slug: str):
        from apps.notifications.templates import ensure_custom_communication_templates

        ensure_custom_communication_templates()
        template = get_object_or_404(get_model('communication', 'CommunicationEventType'), code=slug)
        for field in ['name', 'category', 'email_subject_template', 'email_body_template', 'email_body_html_template', 'sms_template']:
            if field in request.data:
                setattr(template, field, request.data[field])
        template.save()
        return Response({'communication': _communication_payload(template)})


class AdminReportListAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        return Response(
            {
                'results': [
                    {'code': 'orders', 'name': 'Orders', 'description': 'Order totals, status, customer, and placement date.'},
                    {'code': 'products', 'name': 'Products', 'description': 'Catalog visibility, stock, category, and pricing.'},
                    {'code': 'customers', 'name': 'Customers', 'description': 'Customer and staff account status.'},
                    {'code': 'vouchers', 'name': 'Vouchers', 'description': 'Coupon usage and discount totals.'},
                ]
            }
        )


class AdminReportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, report_name: str):
        Order = get_model('order', 'Order')
        Product = get_model('catalogue', 'Product')
        User = get_user_model()
        Voucher = get_model('voucher', 'Voucher')
        StockRecord = get_model('partner', 'StockRecord')

        if report_name == 'orders':
            queryset = Order.objects.select_related('user').order_by('-date_placed')
            return Response(
                {
                    'report': report_name,
                    'summary': {
                        'orders': queryset.count(),
                        'revenue': _decimal(queryset.aggregate(total=Sum('total_incl_tax'))['total']),
                        'by_status': list(queryset.values('status').annotate(count=Count('id')).order_by('status')),
                    },
                    **_page(
                        request,
                        queryset,
                        lambda order: {
                            'id': order.id,
                            'number': order.number,
                            'status': order.status,
                            'customer': getattr(order.user, 'email', '') if order.user_id else '',
                            'total_incl_tax': _decimal(order.total_incl_tax),
                            'currency': order.currency,
                            'date_placed': order.date_placed,
                        },
                    ),
                }
            )

        if report_name == 'products':
            queryset = Product.objects.exclude(structure='parent').prefetch_related('categories', 'stockrecords').order_by('title')
            return Response(
                {
                    'report': report_name,
                    'summary': {
                        'products': queryset.count(),
                        'public_products': queryset.filter(is_public=True).count(),
                        'draft_products': queryset.filter(is_public=False).count(),
                        'stock_units': StockRecord.objects.aggregate(total=Sum('num_in_stock'))['total'] or 0,
                    },
                    **_page(
                        request,
                        queryset,
                        lambda product: {
                            'id': product.id,
                            'title': product.title,
                            'upc': product.upc,
                            'is_public': product.is_public,
                            'category': product.categories.first().name if product.categories.exists() else '',
                            'stock': sum((row.num_in_stock or 0) for row in product.stockrecords.all()),
                            'date_updated': product.date_updated,
                        },
                    ),
                }
            )

        if report_name == 'customers':
            queryset = User.objects.order_by('-date_joined')
            return Response(
                {
                    'report': report_name,
                    'summary': {
                        'customers': queryset.filter(is_staff=False).count(),
                        'staff': queryset.filter(is_staff=True).count(),
                        'active': queryset.filter(is_active=True).count(),
                    },
                    **_page(
                        request,
                        queryset,
                        lambda user: {
                            'id': user.id,
                            'email': user.email,
                            'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'is_staff': user.is_staff,
                            'is_active': user.is_active,
                            'date_joined': user.date_joined,
                        },
                    ),
                }
            )

        if report_name == 'vouchers':
            queryset = Voucher.objects.prefetch_related('offers').order_by('-date_created')
            return Response(
                {
                    'report': report_name,
                    'summary': {
                        'vouchers': queryset.count(),
                        'basket_additions': queryset.aggregate(total=Sum('num_basket_additions'))['total'] or 0,
                        'redemptions': queryset.aggregate(total=Sum('num_orders'))['total'] or 0,
                        'discount': _decimal(queryset.aggregate(total=Sum('total_discount'))['total']),
                    },
                    **_page(request, queryset, _voucher_payload),
                }
            )

        return Response(status=status.HTTP_404_NOT_FOUND)
