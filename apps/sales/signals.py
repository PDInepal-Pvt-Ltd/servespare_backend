"""
Signals for Sales App - Handles:
1. Bidirectional synchronization of payment statuses
2. Invoice generation from sales orders
3. Bill creation from invoices
4. Inventory updates
5. Sales ledger synchronization
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


@receiver(post_save, sender='sales.SalesOrderItem')
def auto_create_or_update_invoice_on_item_add(sender, instance, created, **kwargs):
    """
    Auto-create invoice with items when first item is added to order,
    or update existing invoice when items change
    """
    order = instance.order
    
    # Check if invoice exists
    try:
        invoice = order.invoice
        # Invoice exists - update it with the new/updated item
        update_invoice_item(order, instance)
    except:
        # Invoice doesn't exist yet, create it with all current items
        if order.items.exists():
            order.generate_invoice()


def update_invoice_item(order, order_item):
    """Helper to update an invoice item when order item changes"""
    from apps.sales.models import InvoiceItem
    
    if not hasattr(order, 'invoice'):
        return
    
    invoice = order.invoice
    
    # Find or create corresponding invoice item
    invoice_item, created = InvoiceItem.objects.get_or_create(
        invoice=invoice,
        sales_order_item=order_item,
        defaults={
            'tenant': order.tenant,
            'inventory': order_item.inventory,
            'item_name': order_item.item_name,
            'part_number': order_item.part_number,
            'quantity': order_item.quantity,
            'unit_price': order_item.unit_price,
            'discount_percentage': order_item.discount_percentage,
            'discount_amount': order_item.discount_amount,
            'tax_percentage': order_item.tax_percentage,
            'tax_amount': order_item.tax_amount,
            'line_total': order_item.line_total,
            'notes': order_item.notes,
        }
    )
    
    # Update if item changed
    if not created:
        invoice_item.item_name = order_item.item_name
        invoice_item.part_number = order_item.part_number
        invoice_item.quantity = order_item.quantity
        invoice_item.unit_price = order_item.unit_price
        invoice_item.discount_percentage = order_item.discount_percentage
        invoice_item.discount_amount = order_item.discount_amount
        invoice_item.tax_percentage = order_item.tax_percentage
        invoice_item.tax_amount = order_item.tax_amount
        invoice_item.line_total = order_item.line_total
        invoice_item.notes = order_item.notes
        invoice_item.save()


@receiver(post_save, sender='sales.SalesOrderItem')
def recalculate_sales_order_on_item_change(sender, instance, created, **kwargs):
    """
    Recalculate sales order totals when any sales order item changes
    """
    if instance.order:
        instance.order.calculate_totals()


@receiver(post_save, sender='sales.SalesOrderItem')
def sync_sales_order_tenants_branches(sender, instance, created, **kwargs):
    """
    Keep SalesOrder.tenants and SalesOrder.branches in sync with line items.
    Supports orders that include items from multiple tenants/branches.
    """
    order = getattr(instance, 'order', None)
    order_id = getattr(order, 'id', None)
    if not order_id:
        return

    try:
        tenant_ids = (
            order.items.filter(tenant_id__isnull=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )
        branch_ids = (
            order.items.filter(branch_id__isnull=False)
            .values_list('branch_id', flat=True)
            .distinct()
        )
        order.tenants.set(list(tenant_ids))
        order.branches.set(list(branch_ids))
    except Exception:
        # Don't break order save flow if sync fails
        return


@receiver(post_delete, sender='sales.SalesOrderItem')
def recalculate_sales_order_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate sales order totals when a sales order item is deleted
    """
    if instance.order:
        instance.order.calculate_totals()


@receiver(post_delete, sender='sales.SalesOrderItem')
def sync_sales_order_tenants_branches_on_delete(sender, instance, **kwargs):
    """Re-sync SalesOrder.tenants and branches after item deletion."""
    order = getattr(instance, 'order', None)
    order_id = getattr(order, 'id', None)
    if not order_id:
        return
    try:
        tenant_ids = (
            order.items.filter(tenant_id__isnull=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )
        branch_ids = (
            order.items.filter(branch_id__isnull=False)
            .values_list('branch_id', flat=True)
            .distinct()
        )
        order.tenants.set(list(tenant_ids))
        order.branches.set(list(branch_ids))
    except Exception as exc:
        logger.warning(
            "Failed to sync tenants/branches on delete for order %s: %s",
            order_id,
            exc,
        )


@receiver(post_save, sender='sales.InvoiceItem')
def recalculate_invoice_on_item_change(sender, instance, created, **kwargs):
    """
    Recalculate invoice totals when any invoice item changes
    """
    if instance.invoice:
        instance.invoice.calculate_totals()


@receiver(post_save, sender='sales.InvoiceItem')
def sync_invoice_tenants_branches(sender, instance, created, **kwargs):
    """
    Keep Invoice.tenants and Invoice.branches in sync with invoice items.
    """
    invoice = getattr(instance, 'invoice', None)
    if not getattr(invoice, 'id', None):
        return
    try:
        tenant_ids = (
            invoice.items.filter(tenant_id__isnull=False)
            .values_list('tenant_id', flat=True)
            .distinct()
        )
        branch_ids = (
            invoice.items.filter(inventory__branch_id__isnull=False)
            .values_list('inventory__branch_id', flat=True)
            .distinct()
        )
        invoice.tenants.set(list(tenant_ids))
        invoice.branches.set(list(branch_ids))
    except Exception:
        return


@receiver(post_delete, sender='sales.InvoiceItem')
def recalculate_invoice_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate invoice totals when an invoice item is deleted
    """
    if instance.invoice:
        instance.invoice.calculate_totals()


@receiver(post_save, sender='sales.PurchaseItem')
def recalculate_bill_on_item_change(sender, instance, created, **kwargs):
    """
    Recalculate bill amounts when any purchase item changes
    """
    if instance.bill:
        instance.bill.calculate_all_amounts()


@receiver(post_save, sender='sales.PurchaseItem')
def update_bill_ledger_on_item_change(sender, instance, created, **kwargs):
    """
    Update or create the bill's sales ledger entry when purchase items are added/changed.
    This ensures the ledger is created/updated even if the bill was initially created without items.
    """
    from apps.cashandbank.models import AccountLedger
    from decimal import Decimal
    from django.utils import timezone
    
    bill = instance.bill
    if not bill or not bill.tenant:
        return
    
    # Calculate bill total
    bill_total = bill.subtotal - bill.discount_amount
    if bill_total < 0:
        bill_total = Decimal('0.00')
    
    # Quantize to 2 decimal places to avoid validation errors
    bill_total = bill_total.quantize(Decimal('0.01'))
    
    # Only proceed if bill has a positive total
    if bill_total <= 0:
        return
    
    reference_id = str(bill.id)
    customer_name = bill.customer_name or 'Walk-in Customer'
    
    # Check if ledger entry already exists for this bill
    existing_ledger = AccountLedger.objects.filter(
        reference_type='bill',
        reference_id=reference_id,
        ledger_type='sale',
        transaction_type='sale'
    ).first()
    
    if existing_ledger:
        # Update existing ledger entry with new total
        existing_ledger.debit = bill_total
        existing_ledger.description = f"Bill {bill.id} - {customer_name}"
        existing_ledger.save(update_fields=['debit', 'description'])
    else:
        # Create new ledger entry
        AccountLedger.objects.create(
            tenant=bill.tenant,
            branch=bill.branch,
            ledger_type='sale',
            transaction_type='sale',
            debit=bill_total,
            credit=Decimal('0.00'),
            description=f"Bill {bill.id} - {customer_name}",
            reference=f"Bill #{bill.id}",
            reference_type='bill',
            reference_id=reference_id,
            transaction_date=bill.created or timezone.now(),
            performed_by=bill.created_by,
            is_manual_entry=False,
            notes='Auto-generated from bill with purchase items'
        )


@receiver(post_save, sender='sales.PurchaseItem')
def sync_bill_tenants_branches(sender, instance, created, **kwargs):
    """
    Keep Bill.tenants and Bill.branches in sync with purchase items (via inventory).
    """
    bill = getattr(instance, 'bill', None)
    if not getattr(bill, 'id', None):
        return
    try:
        tenant_ids = (
            bill.purchase_items.filter(inventory__tenant_id__isnull=False)
            .values_list('inventory__tenant_id', flat=True)
            .distinct()
        )
        branch_ids = (
            bill.purchase_items.filter(inventory__branch_id__isnull=False)
            .values_list('inventory__branch_id', flat=True)
            .distinct()
        )
        bill.tenants.set(list(tenant_ids))
        bill.branches.set(list(branch_ids))
    except Exception:
        return


@receiver(post_delete, sender='sales.PurchaseItem')
def recalculate_bill_on_item_delete(sender, instance, **kwargs):
    """
    Recalculate bill amounts when a purchase item is deleted
    """
    if instance.bill:
        instance.bill.calculate_all_amounts()


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
        
        # Quantize to 2 decimal places to avoid validation errors
        bill_total = bill_total.quantize(Decimal('0.01'))
        
        # Only create ledger entry if bill has a positive total
        # This prevents validation errors when creating bills without items
        if bill_total > 0:
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
                
                # Quantize to 2 decimal places to avoid validation errors
                bill_total = bill_total.quantize(Decimal('0.01'))
                
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
    Automatically generate invoice when sales order is created (confirmed)
    Then sync all data and items from the sales order
    """
    if created and instance.order_status == 'confirmed':
        # Check if invoice doesn't already exist
        if not hasattr(instance, 'invoice') or not instance.invoice:
            from apps.sales.models import Invoice
            
            # Create empty invoice
            invoice = Invoice.objects.create(
                tenant=instance.tenant,
                customer=instance.customer,
                branch=instance.branch,
                sales_order=instance,
                payment_status='pending',
                created_by=instance.created_by
            )
            
            # Sync data and items from sales order
            invoice.sync_from_sales_order()


@receiver(post_save, sender='sales.Invoice')
def auto_create_bill_from_paid_invoice(sender, instance, created, **kwargs):
    """
    Automatically create bill when invoice is marked as paid.
    Creates a Bill with PurchaseItems transferred from InvoiceItems.
    """
    # Only process if invoice is paid
    if instance.payment_status != 'paid':
        return
    
    # Check if bill already exists
    try:
        if instance.bill:
            return
    except:
        pass
    
    try:
        instance.convert_to_bill()
    except Exception as e:
        # Log but don't fail - bill can be created manually if needed
        print(f"Error creating bill for invoice {instance.invoice_number}: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_save, sender='sales.Bill')
def decrease_inventory_on_bill_paid(sender, instance, created, **kwargs):
    """
    Automatically decrease inventory when bill is paid
    - For new bills created as 'paid' (walk-in): decrease immediately
    - For bills updated to 'paid': decrease when status changes
    
    Checks if inventory was already decreased to avoid duplicates.
    """
    # Skip if inventory already decreased
    if hasattr(instance, '_inventory_decreased') and instance._inventory_decreased:
        return
    
    # Decrease inventory only when bill is paid
    if instance.status == 'paid':
        instance.update_inventory(reduce_quantity=True)
        # Mark as processed to avoid duplicate decreases
        instance._inventory_decreased = True


@receiver(post_save, sender='sales.Invoice')
def decrease_inventory_on_invoice_paid(sender, instance, created, **kwargs):
    """
    Automatically decrease inventory when invoice is marked as paid
    This ensures inventory is updated when payment is received.
    
    Checks if inventory was already decreased to avoid duplicates.
    """
    # Skip if inventory already decreased
    if hasattr(instance, '_inventory_decreased') and instance._inventory_decreased:
        return
    
    # Only process if invoice is paid
    if instance.payment_status == 'paid':
        instance.update_inventory(reduce_quantity=True)
        # Mark as processed to avoid duplicate decreases
        instance._inventory_decreased = True


@receiver(post_save, sender='sales.Invoice')
def restore_inventory_on_invoice_refund(sender, instance, created, **kwargs):
    """
    Automatically restore inventory when invoice is marked as refunded
    This reverses the inventory deduction when payment is refunded.
    """
    # Skip if inventory was never decreased
    if hasattr(instance, '_inventory_restored') and instance._inventory_restored:
        return
    
    # Only process if invoice is refunded
    if instance.payment_status == 'refunded':
        instance.update_inventory(reduce_quantity=False)
        # Mark as processed to avoid duplicate restores
        instance._inventory_restored = True


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
