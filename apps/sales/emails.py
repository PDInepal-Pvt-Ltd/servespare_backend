"""Email helpers for sales-related notifications."""
import logging
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def _format_money(value):
    """Return a currency-friendly string with two decimal places."""
    try:
        return f"{Decimal(value or 0):,.2f}"
    except Exception:
        return str(value)


def _format_quantity(value):
    """Render quantities without trailing zeros when possible."""
    try:
        quantity = Decimal(value)
        if quantity == quantity.to_integral():
            return format(quantity.normalize(), "f")
        return format(quantity, "f")
    except Exception:
        return str(value)


def send_order_confirmation_email(order):
    """Send an order confirmation email using the order-placed template."""
    if not getattr(order, "customer", None) or not order.customer.email:
        logger.info("Skipping confirmation email; no customer email for order %s", getattr(order, "order_number", ""))
        return False

    try:
        order_date = timezone.localtime(order.order_date) if timezone.is_aware(order.order_date) else order.order_date
    except Exception:
        order_date = order.order_date

    items = []
    for item in order.items.select_related("inventory"):
        items.append({
            "item_name": item.item_name,
            "part_number": item.part_number or "N/A",
            "quantity": _format_quantity(item.quantity),
            "unit_price": _format_money(item.unit_price),
            "line_total": _format_money(item.line_total),
        })

    context = {
        "customer_name": order.customer.full_name or order.customer.username,
        "order_number": order.order_number,
        "order_date": order_date.strftime("%B %d, %Y") if order_date else "",
        "items": items,
        "subtotal": _format_money(order.subtotal),
        "discount_amount": _format_money(order.discount_amount),
        "tax_percentage": f"{Decimal(order.tax_percentage or 0):.0f}",
        "tax_amount": _format_money(order.tax_amount),
        "shipping_charges": _format_money(order.shipping_charges),
        "total_amount": _format_money(order.total_amount),
        "delivery_address": order.delivery_address,
        "delivery_city": order.delivery_city,
        "delivery_province": order.delivery_province,
        "delivery_district": order.delivery_district,
        "delivery_pincode": order.delivery_pincode,
    }

    subject = f"Order {order.order_number} confirmed"
    plain_message = (
        f"Hi {context['customer_name']},\n\n"
        f"Your order {order.order_number} has been confirmed.\n"
        f"Order total: {context['total_amount']}\n"
        f"Status: Confirmed\n\n"
        f"Thank you for choosing ServeSpare."
    )

    try:
        html_message = render_to_string("email/order-placed.html", context)
        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.exception("Failed to send confirmation email for order %s: %s", order.order_number, exc)
        return False
