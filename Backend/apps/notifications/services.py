import logging
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


class NotificationService:
    @property
    def model(self):
        return apps.get_model('notifications', 'EmailNotification')

    def send(self, *, event_type: str, to_email: str, subject_template: str, body_template: str, context: dict,
             related_object_type: str = '', related_object_id: str = '', metadata: dict | None = None) -> bool:
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

        subject = render_to_string(subject_template, context).strip().replace('\n', ' ')
        body = render_to_string(body_template, context)

        log = self.model.objects.create(
            event_type=event_type,
            status='pending',
            recipient=to_email,
            subject=subject,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            metadata=metadata or {},
        )

        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
                reply_to=[settings.NOTIFICATION_REPLY_TO_EMAIL] if settings.NOTIFICATION_REPLY_TO_EMAIL else None,
            )
            message.send()
        except Exception as exc:  # pragma: no cover
            log.status = 'failed'
            log.error_message = str(exc)
            log.save(update_fields=['status', 'error_message', 'updated_at'])
            logger.exception('Failed to send %s email to %s', event_type, to_email)
            return False

        log.status = 'sent'
        log.sent_at = timezone.now()
        log.save(update_fields=['status', 'sent_at', 'updated_at'])
        return True

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


def send_account_registration_email(user) -> bool:
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
    )


def send_password_changed_email(user) -> bool:
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
    )


def send_quote_request_notifications(payload: dict, product=None) -> dict:
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
        'sales_recipients': settings.SALES_NOTIFICATION_RECIPIENTS,
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
        )

    internal_results = []
    for recipient in settings.SALES_NOTIFICATION_RECIPIENTS:
        sent = notification_service.send(
            event_type='quote_request_internal',
            to_email=recipient,
            subject_template='emails/quote_request_internal_subject.txt',
            body_template='emails/quote_request_internal_body.txt',
            context=internal_context,
            related_object_type='product' if product else '',
            related_object_id=str(product.id) if product else '',
            metadata={k: v for k, v in payload.items() if k != 'message'},
        )
        internal_results.append({'recipient': recipient, 'sent': sent})

    return {
        'customer_sent': customer_sent,
        'internal': internal_results,
    }


def send_order_confirmation_email(order) -> bool:
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
    )


def send_shipping_update_email(order, *, status_label: str, tracking_reference: str = '', note: str = '') -> bool:
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
    )


def _format_money(amount, currency: str) -> str:
    if amount is None:
        return f'{currency} 0.00'
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    return f'{currency} {amount.quantize(Decimal("0.01"))}'
