from django.conf import settings

from .services import confirm_payment_session


class CardGatewayError(Exception):
    pass


def authorize_card_payment(
    payment_session,
    *,
    payment_token: str,
    card_brand: str = '',
    last4: str = '',
    expiry_month: int | None = None,
    expiry_year: int | None = None,
    holder_name: str = '',
):
    if not settings.CARD_SANDBOX_ENABLED:
        raise CardGatewayError('Card sandbox integration is disabled on this backend.')

    token = (payment_token or '').strip()
    if not token:
        raise CardGatewayError('A card payment token is required.')
    if not _is_test_token(token):
        raise CardGatewayError('Unsupported sandbox card token.')

    masked_last4 = ''.join(ch for ch in str(last4 or '') if ch.isdigit())[-4:]
    payment_session.provider_payload = {
        **payment_session.provider_payload,
        'provider': settings.CARD_PROVIDER_NAME,
        'payment_token': token,
        'card_brand': (card_brand or '').strip().lower(),
        'last4': masked_last4,
        'expiry_month': expiry_month,
        'expiry_year': expiry_year,
        'holder_name': (holder_name or '').strip(),
    }
    payment_session.save(update_fields=['provider_payload', 'updated_at'])

    external_reference = f'{settings.CARD_PROVIDER_NAME.upper()}-{payment_session.reference}'
    return confirm_payment_session(
        payment_session,
        success=True,
        external_reference=external_reference,
        metadata={
            'card_authorized': True,
            'card_brand': payment_session.provider_payload.get('card_brand', ''),
            'last4': masked_last4,
        },
    )


def _is_test_token(token: str) -> bool:
    return token.startswith('tok_') or token.startswith('pm_') or token.startswith('card_')
