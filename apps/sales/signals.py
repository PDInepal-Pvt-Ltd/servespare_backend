"""
Signals for Sales App - Handles bidirectional synchronization of payment statuses
between Sales Orders, Invoices, and Bills, and syncs bills to sales ledger
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError


@receiver(post_save, sender='sales.Bill')
def sync_bill_to_sales_ledger(sender, instance, created, **kwargs):
    """
    Sync bill to sales ledger when bill is created or status changes.
    Creates ledger entries when bill is in 'paid' or 'credit_sale' status.
    """
    # Sales ledger support removed; no-op.
    return


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


@receiver(post_save, sender='sales.Bill')
def decrease_inventory_on_bill_creation(sender, instance, created, **kwargs):
    """
    Automatically decrease inventory when a bill is created
    Inventory is decreased when bill is created (regardless of status)
    """
    if created:
        # Bill was just created, decrease inventory for all purchase items
        instance.decrease_inventory()


@receiver(post_save, sender='sales.PurchaseItem')
def decrease_inventory_on_purchase_item_creation(sender, instance, created, **kwargs):
    """
    Automatically decrease inventory when a purchase item is added to a bill
    """
    if created and instance.inventory and instance.quantity > 0:
        from decimal import Decimal
        # Decrease inventory immediately when purchase item is created
        # Convert quantity to Decimal to avoid type mismatch
        quantity_to_decrease = Decimal(str(instance.quantity))
        instance.inventory.quantity = max(
            Decimal('0.00'),
            instance.inventory.quantity - quantity_to_decrease
        )
        instance.inventory.save(update_fields=['quantity', 'modified'])


def ready():
    """
    Called when Django app is ready
    """
    pass
