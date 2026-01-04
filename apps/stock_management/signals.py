"""
Signals for Stock Management App - Handles purchase order synchronization to purchase ledger
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from apps.cashandbank.ledger_service import LedgerService

logger = logging.getLogger(__name__)


@receiver(post_save, sender='stock_management.PurchaseOrder')
def sync_purchase_order_to_purchase_ledger(sender, instance, created, **kwargs):
    """
    Sync purchase order to purchase ledger.
    - Creates ledger entry automatically when PO is created
    - Updates ledger entries when PO status changes
    - Removes ledger entries if PO is cancelled/rejected
    """
    try:
        from apps.cashandbank.models import AccountLedger
        from decimal import Decimal
        from django.utils import timezone
        
        if not instance.tenant:
            logger.warning("Purchase order %s missing tenant; skipping ledger entry", instance.id)
            return
        
        reference_id = str(instance.id)
        
        # For newly created POs, create a purchase ledger entry
        if created:
            po_total = instance.total_amount or Decimal('0.00')
            supplier_name = instance.supplier.party_name if instance.supplier else 'Unknown Supplier'
            description = f"Purchase Order {instance.po_number or instance.id} from {supplier_name}"
            reference = f"PO #{instance.po_number or instance.id}"
            
            # Create ledger entry for the purchase (credit entry - outflow)
            AccountLedger.objects.create(
                tenant=instance.tenant,
                branch=instance.branch,
                ledger_type='purchase',
                transaction_type='purchase',
                debit=Decimal('0.00'),
                credit=po_total,
                description=description,
                reference=reference,
                reference_type='purchase_order',
                reference_id=reference_id,
                transaction_date=instance.order_date or timezone.now(),
                performed_by=instance.created_by if hasattr(instance, 'created_by') else None,
                is_manual_entry=False,
                notes='Auto-generated from purchase order creation'
            )
            logger.info("Created purchase ledger entry for PO %s", instance.po_number or instance.id)
        else:
            # Handle status changes - if cancelled/rejected, remove ledger entries
            if instance.status in ['cancelled', 'rejected']:
                deleted_count, _ = AccountLedger.objects.filter(
                    reference_type='purchase_order',
                    reference_id=reference_id,
                    ledger_type='purchase'
                ).delete()
                
                if deleted_count:
                    logger.info("Removed %d ledger entries for cancelled PO %s", deleted_count, instance.po_number or instance.id)
                    # Recalculate running balance after deletion
                    LedgerService._recalculate_running_balance(
                        instance.tenant,
                        instance.branch,
                        'purchase'
                    )
            elif instance.status == 'returned':
                # Create a return/refund entry if return happens
                existing_return = AccountLedger.objects.filter(
                    reference_type='purchase_order',
                    reference_id=reference_id,
                    ledger_type='purchase',
                    transaction_type='refund'
                ).exists()
                
                if not existing_return:
                    po_total = instance.total_amount or Decimal('0.00')
                    supplier_name = instance.supplier.party_name if instance.supplier else 'Unknown Supplier'
                    description = f"Return for PO {instance.po_number or instance.id} from {supplier_name}"
                    reference = f"Return #{instance.po_number or instance.id}"
                    
                    # Create return entry (debit entry - inflow from return)
                    AccountLedger.objects.create(
                        tenant=instance.tenant,
                        branch=instance.branch,
                        ledger_type='purchase',
                        transaction_type='refund',
                        debit=po_total,
                        credit=Decimal('0.00'),
                        description=description,
                        reference=reference,
                        reference_type='purchase_order',
                        reference_id=reference_id,
                        transaction_date=timezone.now(),
                        performed_by=instance.modified_by if hasattr(instance, 'modified_by') else None,
                        is_manual_entry=False,
                        notes='Auto-generated from purchase order return'
                    )
                    logger.info("Created return entry for PO %s", instance.po_number or instance.id)
    except Exception as exc:
        logger.error(
            "Failed to sync PurchaseOrder %s to purchase ledger: %s",
            getattr(instance, 'id', None),
            exc,
            exc_info=True,
        )
