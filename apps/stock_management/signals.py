"""
Signals for Stock Management App - Handles purchase order synchronization to purchase ledger
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='stock_management.PurchaseOrder')
def sync_purchase_order_to_purchase_ledger(sender, instance, created, **kwargs):
    """
    Sync purchase order to purchase ledger when PO is created or status changes.
    Creates ledger entries when PO is in 'received' or 'billed' status.
    """
    from apps.cashandbank.ledger_service import LedgerService
    
    # Sync to purchase ledger based on PO status
    LedgerService.sync_purchase_order_to_purchase_ledger(instance)
