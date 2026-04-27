from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_order_emails(order):
    _send_client_confirmation(order)
    _send_vendor_notification(order)


def _send_client_confirmation(order):
    html = render_to_string('orders/email_client.html', {'order': order})
    txt  = render_to_string('orders/email_client.txt',  {'order': order})
    msg  = EmailMultiAlternatives(
        subject   = 'Frigo Chascomús — Recibimos tu pedido ✓',
        body      = txt,
        from_email= settings.DEFAULT_FROM_EMAIL,
        to        = [order.customer_email],
    )
    msg.attach_alternative(html, 'text/html')
    try:
        msg.send()
    except Exception as e:
        logger.error(f'Error email cliente: {e}')


def _send_vendor_notification(order):
    html = render_to_string('orders/email_vendor.html', {'order': order})
    txt  = render_to_string('orders/email_vendor.txt',  {'order': order})
    msg  = EmailMultiAlternatives(
        subject    = f'🛒 Nuevo pedido — {order.customer_name} ({order.total_items} productos)',
        body       = txt,
        from_email = settings.DEFAULT_FROM_EMAIL,
        to         = [settings.VENTAS_EMAIL],
        reply_to   = [order.customer_email],
    )
    msg.attach_alternative(html, 'text/html')
    try:
        msg.send()
    except Exception as e:
        logger.error(f'Error email vendedor: {e}')
