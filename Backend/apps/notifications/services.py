import logging
from decimal import Decimal
from urllib.parse import urlencode

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.tokens import email_verification_token_generator
from apps.common.async_utils import dispatch_background_task
from .config import build_email_connection, configured_from_email, configured_reply_to_email, configured_sales_recipients
from .templates import ensure_custom_communication_templates

logger = logging.getLogger(__name__)


def _render_template_string(source: str, context: dict) -> str:
    return Template(source).render(Context(context))


def _render_email_content(*, event_type: str, subject_template: str, body_template: str, context: dict) -> tuple[str, str, str]:
    try:
        ensure_custom_communication_templates()
        CommunicationEventType = apps.get_model('communication', 'CommunicationEventType')
        template = CommunicationEventType.objects.filter(code=event_type).first()
    except Exception:
        template = None

    if template and (template.email_subject_template or template.email_body_template or template.email_body_html_template):
        subject = _render_template_string(template.email_subject_template or '', context).strip().replace('\n', ' ')
        body = _render_template_string(template.email_body_template or '', context)
        html_body = _render_template_string(template.email_body_html_template or '', context) if template.email_body_html_template else ''
        return subject, body, html_body

    subject = render_to_string(subject_template, context).strip().replace('\n', ' ')
    body = render_to_string(body_template, context)
    return subject, body, ''


class NotificationService:
    @property
    def model(self):
        return apps.get_model('notifications', 'EmailNotification')

    def send(
        self,
        *,
        event_type: str,
        to_email: str,
        subject_template: str,
        body_template: str,
        context: dict,
        related_object_type: str = '',
        related_object_id: str = '',
        metadata: dict | None = None,
        raise_on_failure: bool = False,
    ) -> bool:
        normalized_email = (to_email or '').strip().lower()
        if not to_email:
            return self._log_skip(
                event_type=event_type,
                recipient='',
                subject='',
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                metadata=metadata or {},
                error_message='Missing recipient email address.',
            )
        if self._is_suppressed(normalized_email):
            return self._log_skip(
                event_type=event_type,
                recipient=normalized_email,
                subject='',
                related_object_type=related_object_type,
                related_object_id=related_object_id,
                metadata={**(metadata or {}), 'suppressed': True},
                error_message='Recipient is on the email suppression list.',
            )

        subject, body, html_body = _render_email_content(
            event_type=event_type,
            subject_template=subject_template,
            body_template=body_template,
            context=context,
        )

        log = self.model.objects.create(
            event_type=event_type,
            status='pending',
            recipient=normalized_email,
            subject=subject,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            metadata=metadata or {},
        )

        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=configured_from_email(),
                to=[normalized_email],
                reply_to=[configured_reply_to_email()] if configured_reply_to_email() else None,
                connection=build_email_connection(),
            )
            if html_body:
                message.attach_alternative(html_body, 'text/html')
            message.send()
        except Exception as exc:  # pragma: no cover
            log.status = 'failed'
            log.error_message = str(exc)
            log.save(update_fields=['status', 'error_message', 'updated_at'])
            logger.exception('Failed to send %s email to %s', event_type, normalized_email)
            if raise_on_failure:
                raise
            return False

        log.status = 'sent'
        log.sent_at = timezone.now()
        log.save(update_fields=['status', 'sent_at', 'updated_at'])
        return True

    def _is_suppressed(self, email: str) -> bool:
        if not email:
            return False
        EmailSuppression = apps.get_model('notifications', 'EmailSuppression')
        return EmailSuppression.objects.filter(email__iexact=email).exists()

    def _log_skip(
        self,
        *,
        event_type: str,
        recipient: str,
        subject: str,
        related_object_type: str,
        related_object_id: str,
        metadata: dict,
        error_message: str,
    ) -> bool:
        self.model.objects.create(
            event_type=event_type,
            status='skipped',
            recipient=recipient,
            subject=subject,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            metadata=metadata,
            error_message=error_message,
        )
        return False


notification_service = NotificationService()


def _display_name_for_user(user) -> str:
    full_name = ' '.join(part for part in [user.first_name, user.last_name] if part).strip()
    return full_name or user.username or user.email


def _user_allows_order_updates(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return True
    profile = getattr(user, 'customer_profile', None)
    return getattr(profile, 'receive_order_updates', True)


def send_account_registration_email(user, *, raise_on_failure: bool = False) -> bool:
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'user': user,
        'display_name': _display_name_for_user(user),
    }
    return notification_service.send(
        event_type='account_registered',
        to_email=user.email,
        subject_template='emails/account_registered_subject.txt',
        body_template='emails/account_registered_body.txt',
        context=context,
        related_object_type='user',
        related_object_id=str(user.id),
        metadata={'email': user.email},
        raise_on_failure=raise_on_failure,
    )


def queue_account_registration_email(user) -> None:
    from .tasks import send_account_registration_email_task

    dispatch_background_task(send_account_registration_email_task, run_kwargs={'user_id': user.id})


def build_email_verification_url(user) -> str:
    base_url = getattr(settings, 'STOREFRONT_BASE_URL', '').rstrip('/') or 'http://localhost:5173'
    query = urlencode(
        {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': email_verification_token_generator.make_token(user),
        }
    )
    return f'{base_url}/account/verify-email?{query}'


def build_password_reset_url(user) -> str:
    base_url = getattr(settings, 'STOREFRONT_BASE_URL', '').rstrip('/') or 'http://localhost:5173'
    query = urlencode(
        {
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        }
    )
    return f'{base_url}/reset-password?{query}'


def send_email_verification_email(user, *, raise_on_failure: bool = False) -> bool:
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'user': user,
        'display_name': _display_name_for_user(user),
        'verification_url': build_email_verification_url(user),
    }
    return notification_service.send(
        event_type='email_verification',
        to_email=user.email,
        subject_template='emails/email_verification_subject.txt',
        body_template='emails/email_verification_body.txt',
        context=context,
        related_object_type='user',
        related_object_id=str(user.id),
        metadata={'email': user.email},
        raise_on_failure=raise_on_failure,
    )


def queue_email_verification_email(user) -> None:
    from .tasks import send_email_verification_email_task

    dispatch_background_task(send_email_verification_email_task, run_kwargs={'user_id': user.id})


def send_password_reset_email(user, *, raise_on_failure: bool = False) -> bool:
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'user': user,
        'display_name': _display_name_for_user(user),
        'reset_url': build_password_reset_url(user),
    }
    return notification_service.send(
        event_type='password_reset',
        to_email=user.email,
        subject_template='emails/password_reset_subject.txt',
        body_template='emails/password_reset_body.txt',
        context=context,
        related_object_type='user',
        related_object_id=str(user.id),
        metadata={'email': user.email},
        raise_on_failure=raise_on_failure,
    )


def queue_password_reset_email(user) -> None:
    from .tasks import send_password_reset_email_task

    dispatch_background_task(send_password_reset_email_task, run_kwargs={'user_id': user.id})


def send_email_two_factor_code(user, *, code: str, raise_on_failure: bool = False) -> bool:
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'user': user,
        'display_name': _display_name_for_user(user),
        'code': code,
    }
    return notification_service.send(
        event_type='email_two_factor',
        to_email=user.email,
        subject_template='emails/email_two_factor_subject.txt',
        body_template='emails/email_two_factor_body.txt',
        context=context,
        related_object_type='user',
        related_object_id=str(user.id),
        metadata={'email': user.email},
        raise_on_failure=raise_on_failure,
    )


def queue_email_two_factor_code(user, *, code: str) -> None:
    from .tasks import send_email_two_factor_code_task

    dispatch_background_task(send_email_two_factor_code_task, run_kwargs={'user_id': user.id, 'code': code})


def send_password_changed_email(user, *, raise_on_failure: bool = False) -> bool:
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'user': user,
        'display_name': _display_name_for_user(user),
    }
    return notification_service.send(
        event_type='password_changed',
        to_email=user.email,
        subject_template='emails/password_changed_subject.txt',
        body_template='emails/password_changed_body.txt',
        context=context,
        related_object_type='user',
        related_object_id=str(user.id),
        metadata={'email': user.email},
        raise_on_failure=raise_on_failure,
    )


def queue_password_changed_email(user) -> None:
    from .tasks import send_password_changed_email_task

    dispatch_background_task(send_password_changed_email_task, run_kwargs={'user_id': user.id})


def send_quote_request_notifications(payload: dict, product=None, *, raise_on_failure: bool = False) -> dict:
    customer_context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'name': payload.get('name', '').strip() or 'Customer',
        'email': payload.get('email', '').strip(),
        'phone': payload.get('phone', '').strip(),
        'company': payload.get('company', '').strip(),
        'message': payload.get('message', '').strip(),
        'product': product,
    }
    internal_context = {
        **customer_context,
        'sales_recipients': configured_sales_recipients(),
    }

    customer_sent = False
    customer_email = customer_context['email']
    if customer_email:
        customer_sent = notification_service.send(
            event_type='quote_request_customer',
            to_email=customer_email,
            subject_template='emails/quote_request_customer_subject.txt',
            body_template='emails/quote_request_customer_body.txt',
            context=customer_context,
            related_object_type='product' if product else '',
            related_object_id=str(product.id) if product else '',
            metadata={k: v for k, v in payload.items() if k != 'message'},
            raise_on_failure=raise_on_failure,
        )

    internal_results = []
    for recipient in configured_sales_recipients():
        sent = notification_service.send(
            event_type='quote_request_internal',
            to_email=recipient,
            subject_template='emails/quote_request_internal_subject.txt',
            body_template='emails/quote_request_internal_body.txt',
            context=internal_context,
            related_object_type='product' if product else '',
            related_object_id=str(product.id) if product else '',
            metadata={k: v for k, v in payload.items() if k != 'message'},
            raise_on_failure=raise_on_failure,
        )
        internal_results.append({'recipient': recipient, 'sent': sent})

    return {
        'customer_sent': customer_sent,
        'internal': internal_results,
    }


def queue_quote_request_notifications(payload: dict, product=None) -> None:
    from .tasks import send_quote_request_notifications_task

    dispatch_background_task(
        send_quote_request_notifications_task,
        run_kwargs={'payload': payload, 'product_id': product.id if product else None},
    )


def send_order_confirmation_email(order, *, raise_on_failure: bool = False) -> bool:
    if getattr(order, 'user_id', None) and not _user_allows_order_updates(order.user):
        return notification_service._log_skip(
            event_type='order_confirmation',
            recipient=getattr(order.user, 'email', '') or '',
            subject='',
            related_object_type='order',
            related_object_id=str(order.number),
            metadata={'order_number': order.number, 'status': order.status, 'preference': 'receive_order_updates'},
            error_message='User disabled order update emails.',
        )

    recipient = order.user.email if getattr(order, 'user_id', None) and getattr(order.user, 'email', '') else order.guest_email
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'order': order,
        'display_name': _display_name_for_user(order.user) if getattr(order, 'user_id', None) else 'Customer',
        'total': _format_money(order.total_incl_tax, order.currency),
        'shipping_total': _format_money(order.shipping_incl_tax, order.currency),
    }
    return notification_service.send(
        event_type='order_confirmation',
        to_email=recipient or '',
        subject_template='emails/order_confirmation_subject.txt',
        body_template='emails/order_confirmation_body.txt',
        context=context,
        related_object_type='order',
        related_object_id=str(order.number),
        metadata={'order_number': order.number, 'status': order.status},
        raise_on_failure=raise_on_failure,
    )


def queue_order_confirmation_email(order) -> None:
    from .tasks import send_order_confirmation_email_task

    dispatch_background_task(send_order_confirmation_email_task, run_kwargs={'order_number': order.number})


def send_shipping_update_email(
    order,
    *,
    status_label: str,
    tracking_reference: str = '',
    note: str = '',
    raise_on_failure: bool = False,
) -> bool:
    if getattr(order, 'user_id', None) and not _user_allows_order_updates(order.user):
        return notification_service._log_skip(
            event_type='shipping_update',
            recipient=getattr(order.user, 'email', '') or '',
            subject='',
            related_object_type='order',
            related_object_id=str(order.number),
            metadata={
                'order_number': order.number,
                'status': order.status,
                'shipping_status': status_label,
                'tracking_reference': tracking_reference,
                'preference': 'receive_order_updates',
            },
            error_message='User disabled order update emails.',
        )

    recipient = order.user.email if getattr(order, 'user_id', None) and getattr(order.user, 'email', '') else order.guest_email
    context = {
        'shop_name': settings.OSCAR_SHOP_NAME,
        'order': order,
        'status_label': status_label,
        'tracking_reference': tracking_reference,
        'note': note,
        'display_name': _display_name_for_user(order.user) if getattr(order, 'user_id', None) else 'Customer',
    }
    return notification_service.send(
        event_type='shipping_update',
        to_email=recipient or '',
        subject_template='emails/shipping_update_subject.txt',
        body_template='emails/shipping_update_body.txt',
        context=context,
        related_object_type='order',
        related_object_id=str(order.number),
        metadata={
            'order_number': order.number,
            'status': order.status,
            'shipping_status': status_label,
            'tracking_reference': tracking_reference,
        },
        raise_on_failure=raise_on_failure,
    )


def queue_shipping_update_email(order, *, status_label: str, tracking_reference: str = '', note: str = '') -> None:
    from .tasks import send_shipping_update_email_task

    dispatch_background_task(
        send_shipping_update_email_task,
        run_kwargs={
            'order_number': order.number,
            'status_label': status_label,
            'tracking_reference': tracking_reference,
            'note': note,
        },
    )


def retry_email_notification(notification, *, raise_on_failure: bool = False) -> bool:
    metadata = notification.metadata or {}
    retry_metadata = {**metadata, 'retry_of': notification.id}

    if notification.event_type in {'account_registered', 'email_verification', 'password_reset', 'password_changed'}:
        User = get_user_model()
        user = User.objects.filter(id=notification.related_object_id).first() or User.objects.filter(email__iexact=notification.recipient).first()
        if not user:
            raise ValueError('Could not find the user for this email log.')
        if notification.event_type == 'account_registered':
            return send_account_registration_email(user, raise_on_failure=raise_on_failure)
        if notification.event_type == 'email_verification':
            return send_email_verification_email(user, raise_on_failure=raise_on_failure)
        if notification.event_type == 'password_reset':
            return send_password_reset_email(user, raise_on_failure=raise_on_failure)
        return send_password_changed_email(user, raise_on_failure=raise_on_failure)

    if notification.event_type == 'email_two_factor':
        raise ValueError('Email 2FA codes cannot be retried from logs. The user must sign in again to generate a fresh code.')

    if notification.event_type == 'order_confirmation':
        Order = apps.get_model('order', 'Order')
        order = Order.objects.filter(number=notification.related_object_id or metadata.get('order_number')).select_related('user').first()
        if not order:
            raise ValueError('Could not find the order for this email log.')
        return send_order_confirmation_email(order, raise_on_failure=raise_on_failure)

    if notification.event_type == 'shipping_update':
        Order = apps.get_model('order', 'Order')
        order = Order.objects.filter(number=notification.related_object_id or metadata.get('order_number')).select_related('user').first()
        if not order:
            raise ValueError('Could not find the order for this email log.')
        return send_shipping_update_email(
            order,
            status_label=metadata.get('shipping_status') or metadata.get('status') or order.status,
            tracking_reference=metadata.get('tracking_reference') or '',
            note=metadata.get('note') or '',
            raise_on_failure=raise_on_failure,
        )

    if notification.event_type in {'quote_request_customer', 'quote_request_internal'}:
        product = None
        if notification.related_object_type == 'product' and notification.related_object_id:
            Product = apps.get_model('catalogue', 'Product')
            product = Product.objects.filter(id=notification.related_object_id).first()
        context = {
            'shop_name': settings.OSCAR_SHOP_NAME,
            'name': metadata.get('name', '').strip() or 'Customer',
            'email': metadata.get('email', '').strip() or notification.recipient,
            'phone': metadata.get('phone', '').strip(),
            'company': metadata.get('company', '').strip(),
            'message': metadata.get('message', '').strip(),
            'product': product,
            'sales_recipients': configured_sales_recipients(),
        }
        subject_template = (
            'emails/quote_request_customer_subject.txt'
            if notification.event_type == 'quote_request_customer'
            else 'emails/quote_request_internal_subject.txt'
        )
        body_template = (
            'emails/quote_request_customer_body.txt'
            if notification.event_type == 'quote_request_customer'
            else 'emails/quote_request_internal_body.txt'
        )
        return notification_service.send(
            event_type=notification.event_type,
            to_email=notification.recipient,
            subject_template=subject_template,
            body_template=body_template,
            context=context,
            related_object_type=notification.related_object_type,
            related_object_id=notification.related_object_id,
            metadata=retry_metadata,
            raise_on_failure=raise_on_failure,
        )

    raise ValueError(f'Email event {notification.event_type} is not retryable.')


def _format_money(amount, currency: str) -> str:
    if amount is None:
        return f'{currency} 0.00'
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return f'{currency} {amount.quantize(Decimal("0.01"))}'
