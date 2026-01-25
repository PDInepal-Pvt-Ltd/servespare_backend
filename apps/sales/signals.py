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
    Creates ledger entries for every bill when it's created.
    Updates ledger entries if bill status changes to refunded/cancelled.
    """
    from apps.cashandbank.models import AccountLedger
    from decimal import Decimal
    from django.utils import timezone
    
    if not instance.tenant:
        return
    
    # Get or create ledger entry reference
    reference_id = str(instance.id)
    
    # For newly created bills, create a sales ledger entry
    if created:
        # Calculate bill total
        bill_total = instance.subtotal - instance.discount_amount
        if bill_total < 0:
            bill_total = Decimal('0.00')
        
        customer_name = instance.customer_name or 'Walk-in Customer'
        description = f"Bill {instance.id} - {customer_name}"
        reference = f"Bill #{instance.id}"
        
        # Create ledger entry for the sale
        AccountLedger.objects.create(
            tenant=instance.tenant,
            branch=instance.branch,
            ledger_type='sale',
            transaction_type='sale',
            debit=bill_total,
            credit=Decimal('0.00'),
            description=description,
            reference=reference,
            reference_type='bill',
            reference_id=reference_id,
            transaction_date=instance.created or timezone.now(),
            performed_by=instance.created_by,
            is_manual_entry=False,
            notes='Auto-generated from bill creation'
        )
    else:
        # Handle status changes - if refunded, create a refund/return entry
        if instance.status == 'refunded':
            # Check if refund entry already exists
            existing_refund = AccountLedger.objects.filter(
                reference_type='bill',
                reference_id=reference_id,
                ledger_type='sale',
                transaction_type='refund'
            ).exists()
            
            if not existing_refund:
                # Calculate bill total for refund
                bill_total = instance.subtotal - instance.discount_amount
                if bill_total < 0:
                    bill_total = Decimal('0.00')
                
                customer_name = instance.customer_name or 'Walk-in Customer'
                description = f"Refund for Bill {instance.id} - {customer_name}"
                reference = f"Refund #{instance.id}"
                
                # Create refund entry (credit entry for return)
                AccountLedger.objects.create(
                    tenant=instance.tenant,
                    branch=instance.branch,
                    ledger_type='sale',
                    transaction_type='refund',
                    debit=Decimal('0.00'),
                    credit=bill_total,
                    description=description,
                    reference=reference,
                    reference_type='bill',
                    reference_id=reference_id,
                    transaction_date=timezone.now(),
                    performed_by=instance.modified_by if hasattr(instance, 'modified_by') else None,
                    is_manual_entry=False,
                    notes='Auto-generated from bill refund'
                )


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


@receiver(post_save, sender='sales.SalesOrder')
def auto_generate_invoice_from_sales_order(sender, instance, created, **kwargs):
    """
    Automatically generate invoice when sales order is created
    Only for confirmed orders
    """
    if created and instance.order_status == 'confirmed':
        # Check if invoice doesn't already exist
        if not hasattr(instance, 'invoice') or not instance.invoice:
            from apps.sales.models import Invoice, InvoiceItem
            
            # Create invoice
            invoice = Invoice.objects.create(
                tenant=instance.tenant,
                customer=instance.customer,
                branch=instance.branch,
                sales_order=instance,
                subtotal=instance.subtotal,
                discount_percentage=instance.discount_percentage,
                discount_amount=instance.discount_amount,
                tax_percentage=instance.tax_percentage,
                tax_amount=instance.tax_amount,
                shipping_charges=instance.shipping_charges,
                total_amount=instance.total_amount,
                payment_status='pending',
                created_by=instance.created_by
            )
            
            # Create invoice items from sales order items
            for order_item in instance.items.all():
                InvoiceItem.objects.create(
                    tenant=instance.tenant,
                    invoice=invoice,
                    inventory=order_item.inventory,
                    item_name=order_item.item_name,
                    part_number=order_item.part_number,
                    quantity=order_item.quantity,
                    unit_price=order_item.unit_price,
                    discount_percentage=order_item.discount_percentage,
                    discount_amount=order_item.discount_amount,
                    tax_percentage=order_item.tax_percentage,
                    tax_amount=order_item.tax_amount,
                    line_total=order_item.line_total
                )


@receiver(post_save, sender='sales.Invoice')
def auto_create_bill_from_paid_invoice(sender, instance, created, **kwargs):
    """
    Automatically create bill when invoice is marked as paid
    Only for paid invoices without existing bills
    """
    # Only process if invoice is paid
    if instance.payment_status != 'paid':
        return
    
    # Check if bill already exists by querying Bill model directly
    # This avoids the OneToOne relationship issue
    from apps.sales.models import Bill, PurchaseItem
    
    # Query to check if a bill with this invoice already exists
    if Bill.objects.filter(invoice=instance).exists():
        # Bill already exists, do nothing
        return
    
    # Create bill from invoice (without invoice field first)
    bill = Bill(
        tenant=instance.tenant,
        branch=instance.branch,
        created_by=instance.created_by,
        sales_order=instance.sales_order,
        customer_name=instance.customer.full_name or instance.customer.username if instance.customer else 'Online Customer',
        address=instance.sales_order.delivery_address if instance.sales_order else '',
        phone_numbers=getattr(instance.customer, 'phone', '') if instance.customer else '',
        customer_type='retail',
        discount_method='amount',
        discount_value=instance.discount_amount,
        tax_percentage=instance.tax_percentage,
        tax_amount=instance.tax_amount,  # Use the already calculated tax_amount from invoice
        payment_method=instance.payment_method or 'online',
        status='paid'
    )
    
    # Temporarily disable auto-calculation of tax in save method
    bill._skip_tax_calculation = True
    # Save the bill first to get a primary key
    bill.save()
    
    # Now set the invoice relationship
    bill.invoice = instance
    bill.save(update_fields=['invoice'])
    
    # Create purchase items from invoice items
    for invoice_item in instance.items.all():
        PurchaseItem.objects.create(
            bill=bill,
            inventory=invoice_item.inventory,
            quantity=invoice_item.quantity,
            price=invoice_item.unit_price
        )
    
    # Update sales order status if exists
    if instance.sales_order:
        instance.sales_order.order_status = 'ready_to_pack'
        instance.sales_order.save(update_fields=['order_status', 'modified'])


@receiver(post_save, sender='sales.Bill')
def decrease_inventory_on_bill_paid(sender, instance, created, **kwargs):
    """
    Automatically decrease inventory when bill is paid
    - For new bills created as 'paid' (walk-in): decrease immediately
    - For bills updated to 'paid': decrease when status changes
    """
    # Skip if inventory already decreased
    if hasattr(instance, '_inventory_decreased') and instance._inventory_decreased:
        return
    
    # Decrease inventory only when bill is paid
    if instance.status == 'paid':
        instance.decrease_inventory()
        # Mark as processed to avoid duplicate decreases
        instance._inventory_decreased = True


# Disabled: Email is sent from serializer after items are created
# @receiver(post_save, sender='sales.SalesOrder')
# def send_order_confirmation_on_create(sender, instance, created, **kwargs):
#     """
#     Send confirmation email when a new SalesOrder is created (confirmed).
#     NOTE: Email sending is handled in the serializer after items are created.
#     """
#     if created and instance.order_status == 'confirmed':
#         from apps.sales.emails import send_order_confirmation_email
#         send_order_confirmation_email(instance)


def ready():
    """
    Called when Django app is ready
    """
    pass
