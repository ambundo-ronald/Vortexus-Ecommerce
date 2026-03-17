from decimal import Decimal, InvalidOperation

from django.apps import apps
from django.conf import settings
from oscar.apps.checkout.utils import CheckoutSessionData
from oscar.apps.shipping.methods import FixedPrice, Free, NoShippingRequired

from apps.common.currency import convert_amount, resolve_display_currency
from apps.common.products import serialize_product_card
from apps.inventory.services import available_quantity_for_line, reserved_quantity_for_line
from apps.common.taxes import calculate_checkout_taxes

ZERO = Decimal('0.00')


def _money(value) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value.quantize(Decimal('0.01'))
    return Decimal(str(value)).quantize(Decimal('0.01'))


def _money_payload(value) -> float:
    return float(_money(value))


class DispatchHubPickup(Free):
    code = 'dispatch-hub-pickup'
    name = 'Dispatch Hub Pickup'
    description = 'Collect stocked parts and equipment from the Vortexus dispatch hub.'


class StandardFreight(FixedPrice):
    code = 'standard-freight'
    name = 'Standard Freight'
    description = 'Standard freight for stocked pumps, filters, treatment systems, and accessories.'


class PriorityDispatch(FixedPrice):
    code = 'priority-dispatch'
    name = 'Priority Dispatch'
    description = 'Priority dispatch for urgent replacements and service-critical equipment.'


class ProjectLogistics(FixedPrice):
    code = 'project-logistics'
    name = 'Project Logistics'
    description = 'Coordinated site delivery for larger borehole, pumping, and treatment projects.'


class IndustrialShippingRepository:
    LOCAL_COUNTRIES = {'KE'}

    def get_shipping_methods(self, basket, shipping_addr=None, **kwargs):
        if not basket.is_shipping_required():
            return [NoShippingRequired()]

        country_code = shipping_country_code(shipping_addr)
        metrics = basket_shipping_metrics(basket)

        methods = []
        for rule in settings.INDUSTRIAL_SHIPPING_RULES:
            if not shipping_rule_matches(rule, metrics, country_code):
                continue
            methods.append(build_shipping_method_from_rule(rule, metrics, country_code))

        return methods


class RuleBasedShippingMethod(FixedPrice):
    def __init__(self, *, rule: dict, charge: Decimal):
        super().__init__(charge_excl_tax=charge, charge_incl_tax=charge)
        self.rule = rule
        self.code = rule['code']
        self.name = rule['name']
        self.description = rule.get('description', '')
        self.carrier_code = rule.get('carrier_code', '')
        self.service_code = rule.get('service_code', '')
        self.method_type = rule.get('method_type', 'freight')
        self.min_eta_days = rule.get('min_eta_days')
        self.max_eta_days = rule.get('max_eta_days')
        self.is_pickup = bool(rule.get('is_pickup', False))


def _decimal(value, default: Decimal = ZERO) -> Decimal:
    if value in (None, ''):
        return default
    if isinstance(value, Decimal):
        return value.quantize(Decimal('0.01'))
    try:
        return Decimal(str(value)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _product_attribute_map(product) -> dict[str, str]:
    values = {}
    for attribute_value in getattr(product, 'attribute_values', []).all():
        attribute = getattr(attribute_value, 'attribute', None)
        if not attribute:
            continue
        values[attribute.code] = (attribute_value.value_as_text or '').strip()
    return values


def product_shipping_weight_kg(product) -> Decimal:
    attrs = _product_attribute_map(product)
    for code in ('shipping_weight_kg', 'weight_kg', 'weight'):
        value = attrs.get(code)
        if not value:
            continue
        normalized = value.lower().replace('kg', '').strip()
        parsed = _decimal(normalized, default=ZERO)
        if parsed > ZERO:
            return parsed
    return ZERO


def product_shipping_profile(product) -> str:
    attrs = _product_attribute_map(product)
    profile = (attrs.get('shipping_profile') or '').strip().lower()
    if profile:
        return profile

    category_slugs = {category.slug for category in product.categories.all()}
    title = (product.title or '').lower()
    if {'water-treatment', 'boreholes', 'pumps', 'tanks'} & category_slugs:
        return 'project'
    if any(token in title for token in ('borehole', 'treatment system', 'dosing plant', 'tank')):
        return 'project'
    return 'standard'


def basket_shipping_metrics(basket) -> dict:
    lines = list(basket.all_lines())
    total_weight = ZERO
    profiles = set()
    supplier_ids = set()

    for line in lines:
        product = line.product
        stockrecord = getattr(line, 'stockrecord', None)
        if stockrecord and getattr(stockrecord, 'partner_id', None):
            supplier_ids.add(stockrecord.partner_id)
        quantity = Decimal(str(line.quantity or 0))
        total_weight += product_shipping_weight_kg(product) * quantity
        profiles.add(product_shipping_profile(product))

    return {
        'subtotal_excl_tax': basket_subtotal_excl_tax(basket),
        'item_count': sum(line.quantity for line in lines),
        'line_count': len(lines),
        'supplier_count': len(supplier_ids),
        'total_weight_kg': total_weight.quantize(Decimal('0.01')),
        'requires_project_logistics': 'project' in profiles,
    }


def shipping_rule_matches(rule: dict, metrics: dict, country_code: str) -> bool:
    allowed_countries = {code.upper() for code in rule.get('countries', []) if code}
    normalized_country = (country_code or '').strip().upper()
    if allowed_countries and normalized_country and normalized_country not in allowed_countries:
        return False
    if allowed_countries and not normalized_country:
        return False

    max_supplier_groups = rule.get('max_supplier_groups')
    if max_supplier_groups is not None and metrics['supplier_count'] > int(max_supplier_groups):
        return False

    min_weight = _decimal(rule.get('min_weight_kg'))
    if min_weight and metrics['total_weight_kg'] < min_weight:
        return False

    max_weight = _decimal(rule.get('max_weight_kg'))
    if max_weight and metrics['total_weight_kg'] > max_weight:
        return False

    if rule.get('project_only') and not metrics['requires_project_logistics']:
        return False

    if rule.get('exclude_project') and metrics['requires_project_logistics']:
        return False

    return True


def build_shipping_method_from_rule(rule: dict, metrics: dict, country_code: str):
    normalized_country = (country_code or '').strip().upper()
    is_international = bool(normalized_country and normalized_country not in {'KE'})
    subtotal = metrics['subtotal_excl_tax']

    charge = _decimal(rule.get('international_charge' if is_international else 'charge'))

    free_threshold = _decimal(rule.get('free_subtotal_threshold'))
    if free_threshold and subtotal >= free_threshold:
        charge = ZERO

    reduced_threshold = _decimal(rule.get('reduced_charge_threshold'))
    if reduced_threshold and subtotal >= reduced_threshold:
        reduced_key = 'reduced_international_charge' if is_international else 'reduced_charge'
        reduced_charge = _decimal(rule.get(reduced_key))
        if reduced_charge or rule.get(reduced_key) in (0, '0', '0.00'):
            charge = reduced_charge

    if rule['code'] == 'dispatch-hub-pickup':
        method = DispatchHubPickup()
        method.rule = rule
        method.carrier_code = rule.get('carrier_code', '')
        method.service_code = rule.get('service_code', '')
        method.method_type = rule.get('method_type', 'pickup')
        method.min_eta_days = rule.get('min_eta_days')
        method.max_eta_days = rule.get('max_eta_days')
        method.is_pickup = True
        return method

    method_map = {
        'standard-freight': StandardFreight,
        'priority-dispatch': PriorityDispatch,
        'project-logistics': ProjectLogistics,
    }
    method_class = method_map.get(rule['code'])
    if method_class:
        method = method_class(charge_excl_tax=charge, charge_incl_tax=charge)
        method.rule = rule
        method.carrier_code = rule.get('carrier_code', '')
        method.service_code = rule.get('service_code', '')
        method.method_type = rule.get('method_type', 'freight')
        method.min_eta_days = rule.get('min_eta_days')
        method.max_eta_days = rule.get('max_eta_days')
        method.is_pickup = bool(rule.get('is_pickup', False))
        return method

    return RuleBasedShippingMethod(rule=rule, charge=charge)


def shipping_country_code(shipping_address) -> str:
    if not shipping_address or not getattr(shipping_address, 'country_id', None):
        return ''

    try:
        country = shipping_address.country
    except Exception:
        return ''

    return getattr(country, 'iso_3166_1_a2', '') or ''


def basket_currency(basket) -> str:
    return getattr(basket, 'currency', None) or 'USD'


def basket_subtotal(basket) -> Decimal:
    total = getattr(basket, 'total_incl_tax', None)
    if total is None:
        total = getattr(basket, 'total_excl_tax', None)
    return _money(total)


def basket_subtotal_excl_tax(basket) -> Decimal:
    total = getattr(basket, 'total_excl_tax', None)
    if total is None:
        total = getattr(basket, 'total_incl_tax', None)
    return _money(total)


def shipping_charge_for_method(method, basket) -> Decimal:
    if not method:
        return ZERO
    charge = method.calculate(basket)
    amount = getattr(charge, 'incl_tax', None)
    if amount is None:
        amount = getattr(charge, 'excl_tax', None)
    return _money(amount)


def get_checkout_session(request) -> CheckoutSessionData:
    return CheckoutSessionData(request)


def clear_selected_shipping_method(request):
    checkout_data = request.session.get(CheckoutSessionData.SESSION_KEY, {})
    shipping_data = checkout_data.get('shipping', {})
    if 'method_code' in shipping_data:
        del shipping_data['method_code']
        request.session.modified = True


def get_shipping_address(request, basket):
    if not basket.is_shipping_required():
        return None

    checkout_session = get_checkout_session(request)
    address_fields = checkout_session.new_shipping_address_fields()
    if address_fields:
        ShippingAddress = apps.get_model('order', 'ShippingAddress')
        return ShippingAddress(**address_fields)

    address_id = checkout_session.shipping_user_address_id()
    if address_id:
        UserAddress = apps.get_model('address', 'UserAddress')
        try:
            address = UserAddress.objects.get(pk=address_id)
        except UserAddress.DoesNotExist:
            return None

        ShippingAddress = apps.get_model('order', 'ShippingAddress')
        shipping_address = ShippingAddress()
        address.populate_alternative_model(shipping_address)
        return shipping_address

    return None


def get_shipping_methods(request, basket, shipping_address=None):
    repository = IndustrialShippingRepository()
    return repository.get_shipping_methods(
        basket=basket,
        user=request.user,
        shipping_addr=shipping_address,
        request=request,
    )


def get_selected_shipping_method(request, basket, shipping_address=None):
    methods = get_shipping_methods(request, basket, shipping_address=shipping_address)
    if not basket.is_shipping_required() and methods:
        return methods[0]

    selected_code = get_checkout_session(request).shipping_method_code(basket)
    for method in methods:
        if method.code == selected_code:
            return method
    return None


def serialize_country(country) -> dict:
    return {
        'code': country.iso_3166_1_a2,
        'name': country.printable_name or country.name,
    }


def available_shipping_countries() -> list[dict]:
    Country = apps.get_model('address', 'Country')
    queryset = Country.objects.filter(is_shipping_country=True).order_by('display_order', 'name')
    return [serialize_country(country) for country in queryset]


def serialize_shipping_address(address) -> dict | None:
    if not address:
        return None

    country_code = ''
    country_name = ''
    if getattr(address, 'country_id', None):
        try:
            country = address.country
        except Exception:
            country = None
        if country:
            country_code = country.iso_3166_1_a2
            country_name = country.printable_name or country.name

    return {
        'first_name': address.first_name or '',
        'last_name': address.last_name or '',
        'line1': address.line1 or '',
        'line2': address.line2 or '',
        'line3': address.line3 or '',
        'line4': address.line4 or '',
        'state': address.state or '',
        'postcode': address.postcode or '',
        'phone_number': str(address.phone_number or ''),
        'notes': address.notes or '',
        'country_code': country_code,
        'country_name': country_name,
    }


def serialize_shipping_method(method, basket, selected: bool = False, display_currency: str | None = None) -> dict:
    charge = method.calculate(basket)
    incl_tax = getattr(charge, 'incl_tax', None)
    excl_tax = getattr(charge, 'excl_tax', None)
    base_amount = incl_tax if incl_tax is not None else excl_tax
    base_currency = getattr(charge, 'currency', None) or basket_currency(basket)
    display_amount, output_currency = convert_amount(base_amount, base_currency, display_currency)

    return {
        'code': method.code,
        'name': str(method.name),
        'description': str(getattr(method, 'description', '') or ''),
        'carrier_code': getattr(method, 'carrier_code', ''),
        'service_code': getattr(method, 'service_code', ''),
        'method_type': getattr(method, 'method_type', ''),
        'is_pickup': bool(getattr(method, 'is_pickup', False)),
        'eta': {
            'min_days': getattr(method, 'min_eta_days', None),
            'max_days': getattr(method, 'max_eta_days', None),
        },
        'charge': display_amount,
        'currency': output_currency,
        'base_charge': _money_payload(base_amount),
        'base_currency': base_currency,
        'selected': selected,
    }


def serialize_basket_line(line, display_currency: str | None = None) -> dict:
    product = serialize_product_card(line.product, display_currency=display_currency)
    unit_price = line.unit_price_incl_tax
    if unit_price is None:
        unit_price = line.unit_price_excl_tax
    line_total = line.line_price_incl_tax
    if line_total is None:
        line_total = line.line_price_excl_tax

    availability = line.purchase_info.availability
    base_currency = line.price_currency or basket_currency(line.basket)
    display_unit_price, output_currency = convert_amount(unit_price, base_currency, display_currency)
    display_line_total, _ = convert_amount(line_total, base_currency, display_currency)
    product['price'] = display_unit_price
    product['currency'] = output_currency

    return {
        'id': line.id,
        'line_reference': line.line_reference,
        'quantity': line.quantity,
        'reserved_quantity': reserved_quantity_for_line(line),
        'available_quantity': available_quantity_for_line(line),
        'unit_price': display_unit_price,
        'line_total': display_line_total,
        'currency': output_currency,
        'base_unit_price': _money_payload(unit_price),
        'base_line_total': _money_payload(line_total),
        'base_currency': base_currency,
        'product': product,
        'availability': {
            'is_available': bool(getattr(availability, 'is_available_to_buy', False)),
            'message': str(getattr(availability, 'message', '') or ''),
        },
    }


def serialize_basket(basket, display_currency: str | None = None) -> dict:
    lines = [serialize_basket_line(line, display_currency=display_currency) for line in basket.all_lines()]
    subtotal = basket_subtotal(basket)
    display_subtotal, output_currency = convert_amount(subtotal, basket_currency(basket), display_currency)
    return {
        'id': basket.id,
        'status': basket.status,
        'currency': output_currency,
        'is_empty': basket.is_empty,
        'shipping_required': basket.is_shipping_required(),
        'line_count': len(lines),
        'item_count': basket.num_items,
        'lines': lines,
        'totals': {
            'subtotal': display_subtotal,
            'currency': output_currency,
            'base_subtotal': _money_payload(subtotal),
            'base_currency': basket_currency(basket),
        },
    }


def build_checkout_payload(request) -> dict:
    basket = request.basket
    shipping_address = get_shipping_address(request, basket)
    country_code = shipping_country_code(shipping_address)
    display_currency = resolve_display_currency(request, country_code=country_code)
    methods = get_shipping_methods(request, basket, shipping_address=shipping_address)
    selected_method = get_selected_shipping_method(request, basket, shipping_address=shipping_address)
    metrics = basket_shipping_metrics(basket)
    subtotal = basket_subtotal_excl_tax(basket)
    shipping_total = shipping_charge_for_method(selected_method, basket)
    taxes = calculate_checkout_taxes(
        subtotal,
        shipping_total,
        country_code,
        basket=basket,
        shipping_method=selected_method,
    )
    tax_total = _money(taxes['total_tax'])
    order_total = subtotal + shipping_total + tax_total
    display_subtotal, output_currency = convert_amount(subtotal, basket_currency(basket), display_currency)
    display_shipping_total, _ = convert_amount(shipping_total, basket_currency(basket), display_currency)
    display_tax_total, _ = convert_amount(tax_total, basket_currency(basket), display_currency)
    display_order_total, _ = convert_amount(order_total, basket_currency(basket), display_currency)

    missing = []
    if basket.is_empty:
        missing.append('basket')
    elif basket.is_shipping_required():
        if not shipping_address:
            missing.append('shipping_address')
        if not selected_method:
            missing.append('shipping_method')

    return {
        'basket': serialize_basket(basket, display_currency=display_currency),
        'shipping': {
            'countries': available_shipping_countries(),
            'address': serialize_shipping_address(shipping_address),
            'shipping_required': basket.is_shipping_required(),
            'display_currency': output_currency,
            'metrics': {
                'item_count': metrics['item_count'],
                'line_count': metrics['line_count'],
                'supplier_count': metrics['supplier_count'],
                'total_weight_kg': _money_payload(metrics['total_weight_kg']),
                'requires_project_logistics': metrics['requires_project_logistics'],
            },
            'methods': [
                serialize_shipping_method(
                    method,
                    basket,
                    selected=bool(selected_method and method.code == selected_method.code),
                    display_currency=display_currency,
                )
                for method in methods
            ],
            'selected_method': (
                serialize_shipping_method(selected_method, basket, selected=True, display_currency=display_currency)
                if selected_method
                else None
            ),
            'ready_for_checkout': not missing,
            'missing': missing,
            'taxes': taxes,
            'totals': {
                'subtotal': display_subtotal,
                'shipping': display_shipping_total,
                'tax': display_tax_total,
                'order_total': display_order_total,
                'currency': output_currency,
                'base_subtotal': _money_payload(subtotal),
                'base_shipping': _money_payload(shipping_total),
                'base_tax': _money_payload(tax_total),
                'base_order_total': _money_payload(order_total),
                'base_currency': basket_currency(basket),
            },
        },
    }
