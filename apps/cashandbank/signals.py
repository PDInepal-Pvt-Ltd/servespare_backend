"""
Signals for CashBank App - Handles auto-posting of sales to active cashier shifts
and syncing with Account Ledger
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='sales.Bill')
def auto_post_sale_to_shift(sender, instance, created, **kwargs):
    """
    Auto-post sale transaction to active cashier shift if:
    1. Bill is newly created
    2. Payment method is 'cash'
    3. Bill status is 'paid'
    4. A matching active shift exists for the cashier/branch
    
    This handles the auto sales posting workflow described in the shift flow.
    """
    # Only process on creation
    if not created:
        return
    
    # Skip if payment method is not cash
    if instance.payment_method != 'cash':
        return
    
    # Skip if bill status is not paid
    if instance.status != 'paid':
        return
    
    # We need the user context - try to get from request or audit log
    # For now, we'll try to find the user from audit logs or use None
    created_user = None
    
    # Try to find the user from the audit log
    try:
        from apps.base.models import AuditLog
        audit = AuditLog.objects.filter(
            entity='Bill',
            object_id=str(instance.id),
            action='create'
        ).first()
        if audit and audit.user:
            created_user = audit.user
    except Exception as e:
        logger.warning(f"Could not find audit log for bill {instance.id}: {e}")
    
    if not created_user:
        logger.info(f"No user context found for bill {instance.id}, skipping auto-post")
        return
    
    # Find active shift for this cashier and branch
    from apps.cashandbank.models import CashierShift, ShiftTransaction
    
    try:
        with transaction.atomic():
            shift = CashierShift.objects.select_for_update().get(
                cashier=created_user,
                branch=instance.branch,
                tenant=instance.tenant,
                status='open'
            )
            
            # Calculate sale amount
            sale_amount = instance.total_after_discount
            
            if not sale_amount or sale_amount <= 0:
                logger.info(f"Bill {instance.id} has no sale amount, skipping")
                return
            
            sale_amount = Decimal(str(sale_amount))
            
            # Increment expected_amount by sale amount
            shift.expected_amount = (shift.expected_amount or Decimal('0.00')) + sale_amount
            shift.save(update_fields=['expected_amount'])
            
            # Create sale transaction
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=instance.tenant,
                transaction_type='sale',
                amount=sale_amount,
                description=f'Sale from bill {instance.id} to {instance.customer_name}',
                reference_type='bill',
                reference_id=str(instance.id),
                performed_by=created_user
            )
            
            logger.info(f"Auto-posted sale {sale_amount} from bill {instance.id} to shift {shift.id}")
    
    except CashierShift.DoesNotExist:
        logger.info(
            f"No active shift found for user {created_user.username} "
            f"branch {instance.branch}, skipping auto-post"
        )
    except Exception as e:
        logger.error(f"Error auto-posting sale for bill {instance.id}: {e}", exc_info=True)


@receiver(post_save, sender='cashandbank.ShiftTransaction')
def sync_shift_transaction_to_ledger(sender, instance, created, **kwargs):
    """
    Auto-create corresponding AccountLedger entries when ShiftTransaction is created.
    This keeps the ledgers in sync with shift transactions.
    
    Maps transaction types to ledger types:
    - all transactions -> general ledger
    """
    if not created:
        return

    from apps.cashandbank.models import AccountLedger

    try:
        with transaction.atomic():
            # Determine which ledgers to update (sales/purchase ledgers removed)
            ledger_types = ['general']  # All transactions go to general ledger
            
            # Calculate debit and credit based on transaction type
            if instance.transaction_type in ('opening', 'cash_in', 'sale'):
                debit = instance.amount
                credit = Decimal('0.00')
            else:  # cash_out, closing
                debit = Decimal('0.00')
                credit = instance.amount
            
            # Create ledger entries for each applicable ledger type
            for ledger_type in ledger_types:
                # Calculate running balance
                previous_balance = AccountLedger.objects.filter(
                    shift=instance.shift,
                    ledger_type=ledger_type,
                    transaction_date__lt=instance.transaction_date
                ).order_by('-transaction_date', '-id').values_list('balance', flat=True).first() or Decimal('0.00')
                
                running_balance = previous_balance + debit - credit
                
                AccountLedger.objects.create(
                    tenant=instance.tenant,
                    branch=instance.shift.branch,
                    shift=instance.shift,
                    ledger_type=ledger_type,
                    transaction_type=instance.transaction_type,
                    debit=debit,
                    credit=credit,
                    balance=running_balance,
                    description=instance.description or f'{instance.get_transaction_type_display()} transaction',
                    reference=f'Shift #{instance.shift.id}',
                    reference_type='shift',
                    reference_id=str(instance.shift.id),
                    transaction_date=instance.transaction_date,
                    performed_by=instance.performed_by,
                    is_manual_entry=False,
                    notes=f'Auto-synced from ShiftTransaction {instance.id}'
                )
            
            logger.info(
                f"Synced ShiftTransaction {instance.id} to AccountLedger "
                f"for ledger types: {ledger_types}"
            )
    
    except Exception as e:
        logger.error(
            f"Error syncing ShiftTransaction {instance.id} to AccountLedger: {e}",
            exc_info=True
        )

