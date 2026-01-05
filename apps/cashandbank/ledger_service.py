"""
Ledger Service - Handles synchronization of transactions to appropriate ledgers
Provides service layer for creating and managing ledger entries across different ledger types.
"""
from decimal import Decimal
from datetime import datetime, time
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class LedgerService:
    """Service class for managing ledger synchronization"""

    @staticmethod
    def create_sales_ledger_entry(bill, debit_amount=None, credit_amount=None, description=None):
        """
        Create a sales ledger entry for a bill transaction.
        
        Args:
            bill: Bill instance
            debit_amount: Amount to debit (typically bill total)
            credit_amount: Amount to credit (for returns/refunds)
            description: Optional custom description
            
        Returns:
            AccountLedger instance or None
        """
        logger.info("Sales ledger support removed; skipping sales ledger entry creation")
        return None

    @staticmethod
    def create_purchase_ledger_entry(purchase_order, debit_amount=None, credit_amount=None, description=None):
        """
        Create a purchase ledger entry for a purchase order transaction.
        
        Args:
            purchase_order: PurchaseOrder instance
            debit_amount: Amount to debit (typically for returns)
            credit_amount: Amount to credit (typically purchase total)
            description: Optional custom description
            
        Returns:
            AccountLedger instance or None
        """
        from apps.cashandbank.models import AccountLedger

        if not purchase_order:
            logger.warning("No purchase order provided; skipping purchase ledger entry creation")
            return None

        if not purchase_order.tenant:
            logger.warning(
                "Purchase order %s missing tenant; skipping ledger entry",
                getattr(purchase_order, 'id', None),
            )
            return None

        with transaction.atomic():
            reference_id = str(purchase_order.id)
            reference = f"PO #{purchase_order.po_number or purchase_order.id}"
            supplier_name = getattr(purchase_order.supplier, 'party_name', 'Unknown supplier')
            description = description or f"Purchase Order {purchase_order.po_number} from {supplier_name}"
            transaction_date = LedgerService._po_transaction_date(purchase_order)

            credit = LedgerService._normalize_decimal(
                credit_amount if credit_amount is not None else purchase_order.total_amount
            )
            debit = LedgerService._normalize_decimal(debit_amount)

            ledger_qs = AccountLedger.objects.select_for_update().filter(
                reference_type='purchase_order',
                reference_id=reference_id,
                ledger_type='purchase',
            )

            if credit <= 0 and debit <= 0:
                removed, _ = ledger_qs.delete()
                if removed:
                    LedgerService._recalculate_running_balance(
                        purchase_order.tenant,
                        purchase_order.branch,
                        'purchase',
                    )
                logger.info(
                    "Purchase order %s has no amount to record; skipping ledger entry",
                    purchase_order.id,
                )
                return None

            ledger_entry = ledger_qs.first()

            if ledger_entry:
                ledger_entry.debit = debit
                ledger_entry.credit = credit
                ledger_entry.description = description
                ledger_entry.reference = reference
                ledger_entry.transaction_type = 'purchase'
                ledger_entry.ledger_type = 'purchase'
                ledger_entry.reference_type = 'purchase_order'
                ledger_entry.reference_id = reference_id
                ledger_entry.branch = purchase_order.branch
                ledger_entry.tenant = purchase_order.tenant
                ledger_entry.transaction_date = transaction_date
                ledger_entry.performed_by = getattr(purchase_order, 'created_by', None)
                ledger_entry.is_manual_entry = False
                ledger_entry.save()
            else:
                previous_balance = AccountLedger.objects.filter(
                    tenant=purchase_order.tenant,
                    branch=purchase_order.branch,
                    ledger_type='purchase',
                    transaction_date__lte=transaction_date,
                ).order_by('-transaction_date', '-id').values_list('balance', flat=True).first() or Decimal('0.00')

                running_balance = previous_balance + debit - credit

                ledger_entry = AccountLedger.objects.create(
                    tenant=purchase_order.tenant,
                    branch=purchase_order.branch,
                    ledger_type='purchase',
                    transaction_type='purchase',
                    debit=debit,
                    credit=credit,
                    balance=running_balance,
                    description=description,
                    reference=reference,
                    reference_type='purchase_order',
                    reference_id=reference_id,
                    transaction_date=transaction_date,
                    performed_by=getattr(purchase_order, 'created_by', None),
                    is_manual_entry=False,
                    notes='Auto-synced from PurchaseOrder',
                )

            LedgerService._recalculate_running_balance(
                purchase_order.tenant,
                purchase_order.branch,
                'purchase',
            )

            return ledger_entry

    @staticmethod
    def sync_bill_to_sales_ledger(bill):
        """
        Sync a bill to the sales ledger based on its status.
        Creates or removes ledger entries as needed.
        
        Args:
            bill: Bill instance to sync
        """
        logger.info("Sales ledger support removed; skipping sales ledger sync")
        return None

    @staticmethod
    def sync_purchase_order_to_purchase_ledger(purchase_order):
        """
        Sync a purchase order to the purchase ledger based on its status.
        Creates or removes ledger entries as needed.
        
        Args:
            purchase_order: PurchaseOrder instance to sync
        """
        from apps.cashandbank.models import AccountLedger

        if not purchase_order:
            logger.warning("No purchase order supplied for ledger sync")
            return None

        valid_statuses = {'received', 'billed'}

        if purchase_order.status in valid_statuses:
            return LedgerService.create_purchase_ledger_entry(purchase_order)

        with transaction.atomic():
            reference_id = str(purchase_order.id)
            entries = list(
                AccountLedger.objects.select_for_update().filter(
                    reference_type='purchase_order',
                    reference_id=reference_id,
                    ledger_type='purchase',
                ).values('tenant_id', 'branch_id')
            )

            deleted_count, _ = AccountLedger.objects.filter(
                reference_type='purchase_order',
                reference_id=reference_id,
                ledger_type='purchase',
            ).delete()

            if deleted_count:
                for entry in entries:
                    LedgerService._recalculate_running_balance(
                        entry['tenant_id'],
                        entry['branch_id'],
                        'purchase',
                    )

            logger.info(
                "Purchase order %s not in received/billed status (%s); ledger entries removed",
                purchase_order.id,
                purchase_order.status,
            )

        return None

    @staticmethod
    def _normalize_decimal(amount):
        """Safely convert amounts to Decimal."""
        if amount is None:
            return Decimal('0.00')
        if isinstance(amount, Decimal):
            return amount
        try:
            return Decimal(str(amount))
        except Exception:
            return Decimal('0.00')

    @staticmethod
    def _po_transaction_date(purchase_order):
        """Use the purchase order date as the transaction timestamp when available."""
        if getattr(purchase_order, 'order_date', None):
            base_dt = datetime.combine(purchase_order.order_date, time.min)
            if timezone.is_naive(base_dt):
                base_dt = timezone.make_aware(base_dt, timezone.get_current_timezone())
            return base_dt
        return timezone.now()

    @staticmethod
    def _recalculate_running_balance(tenant, branch, ledger_type):
        """Recalculate running balance for a specific ledger scope."""
        from apps.cashandbank.models import AccountLedger

        entries = AccountLedger.objects.select_for_update().filter(
            tenant=tenant,
            branch=branch,
            ledger_type=ledger_type,
        ).order_by('transaction_date', 'id')

        running = Decimal('0.00')
        for entry in entries:
            running = running + entry.debit - entry.credit
            if entry.balance != running:
                entry.balance = running
                entry.save(update_fields=['balance', 'modified'])

        return running
