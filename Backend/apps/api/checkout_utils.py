from decimal import Decimal

from django.apps import apps
from oscar.apps.checkout.utils import CheckoutSessionData
from oscar.apps.shipping.methods import FixedPrice, Free, NoShippingRequired

from apps.common.products import serialize_product_card

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

        subtotal = basket_subtotal(basket)
        country_code = shipping_country_code(shipping_addr)

        if country_code and country_code not in self.LOCAL_COUNTRIES:
            return [
                StandardFreight(charge_excl_tax=Decimal('95.00'), charge_incl_tax=Decimal('95.00')),
                ProjectLogistics(
                    charge_excl_tax=Decimal('260.00') if subtotal < Decimal('3000.00') else Decimal('180.00'),
                    charge_incl_tax=Decimal('260.00') if subtotal < Decimal('3000.00') else Decimal('180.00'),
                ),
            ]

        standard_charge = ZERO if subtotal >= Decimal('1500.00') else Decimal('35.00')
        priority_charge = ZERO if subtotal >= Decimal('2500.00') else Decimal('85.00')
        project_charge = Decimal('180.00') if subtotal < Decimal('3000.00') else Decimal('120.00')

        return [
            DispatchHubPickup(),
            StandardFreight(charge_excl_tax=standard_charge, charge_incl_tax=standard_charge),
            PriorityDispatch(charge_excl_tax=priority_charge, charge_incl_tax=priority_charge),
            ProjectLogistics(charge_excl_tax=project_charge, charge_incl_tax=project_charge),
        ]


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


def serialize_shipping_method(method, basket, selected: bool = False) -> dict:
    charge = method.calculate(basket)
    incl_tax = getattr(charge, 'incl_tax', None)
    excl_tax = getattr(charge, 'excl_tax', None)

    return {
        'code': method.code,
        'name': str(method.name),
        'description': str(getattr(method, 'description', '') or ''),
        'charge': _money_payload(incl_tax if incl_tax is not None else excl_tax),
        'currency': getattr(charge, 'currency', None) or basket_currency(basket),
        'selected': selected,
    }


def serialize_basket_line(line) -> dict:
    product = serialize_product_card(line.product)
    unit_price = line.unit_price_incl_tax
    if unit_price is None:
        unit_price = line.unit_price_excl_tax
    line_total = line.line_price_incl_tax
    if line_total is None:
        line_total = line.line_price_excl_tax

    availability = line.purchase_info.availability
    product['price'] = _money_payload(unit_price)
    product['currency'] = line.price_currency or basket_currency(line.basket)

    return {
        'id': line.id,
        'line_reference': line.line_reference,
        'quantity': line.quantity,
        'unit_price': _money_payload(unit_price),
        'line_total': _money_payload(line_total),
        'currency': line.price_currency or basket_currency(line.basket),
        'product': product,
        'availability': {
            'is_available': bool(getattr(availability, 'is_available_to_buy', False)),
            'message': str(getattr(availability, 'message', '') or ''),
        },
    }


def serialize_basket(basket) -> dict:
    lines = [serialize_basket_line(line) for line in basket.all_lines()]
    subtotal = basket_subtotal(basket)
    return {
        'id': basket.id,
        'status': basket.status,
        'currency': basket_currency(basket),
        'is_empty': basket.is_empty,
        'shipping_required': basket.is_shipping_required(),
        'line_count': len(lines),
        'item_count': basket.num_items,
        'lines': lines,
        'totals': {
            'subtotal': _money_payload(subtotal),
            'currency': basket_currency(basket),
        },
    }


def build_checkout_payload(request) -> dict:
    basket = request.basket
    shipping_address = get_shipping_address(request, basket)
    methods = get_shipping_methods(request, basket, shipping_address=shipping_address)
    selected_method = get_selected_shipping_method(request, basket, shipping_address=shipping_address)
    subtotal = basket_subtotal(basket)
    shipping_total = shipping_charge_for_method(selected_method, basket)
    order_total = subtotal + shipping_total

    missing = []
    if basket.is_empty:
        missing.append('basket')
    elif basket.is_shipping_required():
        if not shipping_address:
            missing.append('shipping_address')
        if not selected_method:
            missing.append('shipping_method')

    return {
        'basket': serialize_basket(basket),
        'shipping': {
            'countries': available_shipping_countries(),
            'address': serialize_shipping_address(shipping_address),
            'shipping_required': basket.is_shipping_required(),
            'methods': [
                serialize_shipping_method(method, basket, selected=bool(selected_method and method.code == selected_method.code))
                for method in methods
            ],
            'selected_method': (
                serialize_shipping_method(selected_method, basket, selected=True) if selected_method else None
            ),
            'ready_for_checkout': not missing,
            'missing': missing,
            'totals': {
                'subtotal': _money_payload(subtotal),
                'shipping': _money_payload(shipping_total),
                'order_total': _money_payload(order_total),
                'currency': basket_currency(basket),
            },
        },
    }
