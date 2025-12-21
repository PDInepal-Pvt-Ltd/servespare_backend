"""
Signals for Sales App - Handles bidirectional synchronization of payment statuses
between Sales Orders, Invoices, and Bills
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError


@receiver(post_save, sender='sales.Invoice')
def sync_invoice_payment_to_sales_order(sender, instance, created, **kwargs):
    """
    Sync invoice payment status changes to sales order
    """
    # Payment model now holds the authoritative payment snapshot; skip legacy sync.
    return
    # Skip if this signal was triggered by a coordinated update
    if getattr(instance, '_skip_signal', False):
        return
    
    if not instance.sales_order:
        return
    
    # Update sales order payment status based on invoice
    payment_status_map = {
        'paid': 'paid',
        'pending': 'pending',
        'on_hold': 'pending',
        'credit_sale': 'credit_sale',
        'cancelled': 'pending',
        'refunded': 'pending',
    }
    
    new_status = payment_status_map.get(instance.payment_status, 'pending')
    
    if instance.sales_order.payment_status != new_status:
        instance.sales_order.payment_status = new_status
        instance.sales_order.paid_amount = instance.paid_amount
        if instance.payment_method:
            instance.sales_order.payment_method = instance.payment_method
        
        # Temporarily disable signals on the target to avoid recursion
        setattr(instance.sales_order, '_skip_signal', True)
        instance.sales_order.save(
            update_fields=['payment_status', 'paid_amount', 'payment_method', 'modified']
        )
        setattr(instance.sales_order, '_skip_signal', False)


@receiver(post_save, sender='sales.Invoice')
def sync_invoice_payment_to_bill(sender, instance, created, **kwargs):
    """
    Sync invoice payment status changes to associated bill
    """
    # Payment model now holds the authoritative payment snapshot; skip legacy sync.
    return


@receiver(post_save, sender='sales.SalesOrder')
def sync_sales_order_payment_to_invoice(sender, instance, created, **kwargs):
    """
    Sync sales order payment status changes to invoice
    """
    # Payment model now holds the authoritative payment snapshot; skip legacy sync.
    return


@receiver(post_save, sender='sales.Bill')
def sync_bill_status_to_invoice(sender, instance, created, **kwargs):
    """
    Sync bill status changes to associated invoice
    """
    # Payment model now holds the authoritative payment snapshot; skip legacy sync.
    return


def ready():
    """
    Called when Django app is ready
    """
    pass
