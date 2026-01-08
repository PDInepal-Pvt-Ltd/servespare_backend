"""
Signals for Stock Management App - Handles purchase order synchronization to purchase ledger
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

from apps.cashandbank.ledger_service import LedgerService
from apps.stock_management.models import PurchaseOrder, PurchaseOrderItem

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PurchaseOrder)
def sync_purchase_order_to_purchase_ledger(sender, instance, created, **kwargs):
    """
    Sync purchase order to purchase ledger using the LedgerService.
    Behavior per docs:
    - On any save, if status in {'received', 'billed'} => create/update entry
    - Otherwise => remove existing entry
    This ensures amounts reflect current PO items and status.
    """
    try:
        if not getattr(instance, 'tenant', None):
            logger.warning("Purchase order %s missing tenant; skipping ledger sync", instance.id)
            return

        LedgerService.sync_purchase_order_to_purchase_ledger(instance)
    except Exception as exc:
        logger.error(
            "Failed to sync PurchaseOrder %s to purchase ledger: %s",
            getattr(instance, 'id', None),
            exc,
            exc_info=True,
        )


@receiver(post_save, sender=PurchaseOrderItem)
def update_ledger_on_item_change(sender, instance, created, **kwargs):
    """
    When PO items are added/updated, refresh the ledger entry if the
    parent PO is already in a ledger-eligible status.
    """
    try:
        po = getattr(instance, 'purchase_order', None)
        if not po or not getattr(po, 'tenant', None):
            return

        if po.status in {'received', 'billed'}:
            LedgerService.create_purchase_ledger_entry(po)
    except Exception as exc:
        logger.error(
            "Failed to update ledger on item change for PO %s: %s",
            getattr(getattr(instance, 'purchase_order', None), 'id', None),
            exc,
            exc_info=True,
        )


@receiver(post_delete, sender=PurchaseOrderItem)
def update_ledger_on_item_delete(sender, instance, **kwargs):
    """
    When PO items are deleted, refresh the ledger entry if the parent
    PO is already in a ledger-eligible status.
    """
    try:
        po = getattr(instance, 'purchase_order', None)
        if not po or not getattr(po, 'tenant', None):
            return

        if po.status in {'received', 'billed'}:
            LedgerService.create_purchase_ledger_entry(po)
    except Exception as exc:
        logger.error(
            "Failed to update ledger on item delete for PO %s: %s",
            getattr(getattr(instance, 'purchase_order', None), 'id', None),
            exc,
            exc_info=True,
        )
