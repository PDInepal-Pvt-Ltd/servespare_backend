"""
Ledger Service - Handles synchronization of transactions to appropriate ledgers
Provides service layer for creating and managing ledger entries across different ledger types.
"""
from decimal import Decimal
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
        from apps.cashandbank.models import AccountLedger
        
        if not bill.tenant:
            logger.warning(f"Bill {bill.id} has no tenant, skipping ledger entry")
            return None
        
        try:
            with transaction.atomic():
                # Calculate amounts if not provided
                if debit_amount is None and credit_amount is None:
                    total_after_discount = bill.total_after_discount or Decimal('0.00')
                    if total_after_discount > 0:
                        debit_amount = Decimal(str(total_after_discount))
                    else:
                        debit_amount = Decimal('0.00')
                    credit_amount = Decimal('0.00')
                
                # Ensure we have Decimal values
                debit_amount = Decimal(str(debit_amount or '0.00'))
                credit_amount = Decimal(str(credit_amount or '0.00'))
                
                if debit_amount <= Decimal('0.00') and credit_amount <= Decimal('0.00'):
                    logger.info(f"Bill {bill.id} has no amount to record, skipping")
                    return None
                
                # Build description
                if not description:
                    description = f"Sales from Bill #{bill.id} - {bill.customer_name} ({bill.get_customer_type_display()})"
                
                # Get previous balance for this tenant and ledger type
                previous_ledger = AccountLedger.objects.filter(
                    tenant=bill.tenant,
                    branch=bill.branch,
                    ledger_type='sales'
                ).order_by('-transaction_date', '-id').first()
                
                previous_balance = previous_ledger.balance if previous_ledger else Decimal('0.00')
                running_balance = previous_balance + debit_amount - credit_amount
                
                # Create ledger entry
                ledger_entry = AccountLedger.objects.create(
                    tenant=bill.tenant,
                    branch=bill.branch,
                    ledger_type='sales',
                    transaction_type='sale',
                    debit=debit_amount,
                    credit=credit_amount,
                    balance=running_balance,
                    description=description,
                    reference=f"Bill #{bill.id}",
                    reference_type='bill',
                    reference_id=str(bill.id),
                    transaction_date=timezone.now(),
                    performed_by=None,  # Could be enhanced to capture user
                    is_manual_entry=False
                )
                
                logger.info(f"Created sales ledger entry {ledger_entry.id} for bill {bill.id}")
                return ledger_entry
                
        except Exception as e:
            logger.error(f"Error creating sales ledger entry for bill {bill.id}: {e}", exc_info=True)
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
        
        if not purchase_order.tenant:
            logger.warning(f"Purchase Order {purchase_order.id} has no tenant, skipping ledger entry")
            return None
        
        try:
            with transaction.atomic():
                # Calculate amounts if not provided
                if debit_amount is None and credit_amount is None:
                    total_amount = purchase_order.total_amount or Decimal('0.00')
                    debit_amount = Decimal('0.00')
                    if total_amount > 0:
                        credit_amount = Decimal(str(total_amount))
                    else:
                        credit_amount = Decimal('0.00')
                
                # Ensure we have Decimal values
                debit_amount = Decimal(str(debit_amount or '0.00'))
                credit_amount = Decimal(str(credit_amount or '0.00'))
                
                if debit_amount <= Decimal('0.00') and credit_amount <= Decimal('0.00'):
                    logger.info(f"Purchase Order {purchase_order.id} has no amount to record, skipping")
                    return None
                
                # Build description
                if not description:
                    description = f"Purchase Order #{purchase_order.po_number} from {purchase_order.supplier.party_name}"
                
                # Get previous balance for this tenant and ledger type
                previous_ledger = AccountLedger.objects.filter(
                    tenant=purchase_order.tenant,
                    branch=purchase_order.branch,
                    ledger_type='purchase'
                ).order_by('-transaction_date', '-id').first()
                
                previous_balance = previous_ledger.balance if previous_ledger else Decimal('0.00')
                running_balance = previous_balance + debit_amount - credit_amount
                
                # Create ledger entry
                ledger_entry = AccountLedger.objects.create(
                    tenant=purchase_order.tenant,
                    branch=purchase_order.branch,
                    ledger_type='purchase',
                    transaction_type='purchase',
                    debit=debit_amount,
                    credit=credit_amount,
                    balance=running_balance,
                    description=description,
                    reference=f"PO #{purchase_order.po_number}",
                    reference_type='purchase_order',
                    reference_id=str(purchase_order.id),
                    transaction_date=timezone.now(),
                    performed_by=None,  # Could be enhanced to capture user
                    is_manual_entry=False
                )
                
                logger.info(f"Created purchase ledger entry {ledger_entry.id} for PO {purchase_order.po_number}")
                return ledger_entry
                
        except Exception as e:
            logger.error(f"Error creating purchase ledger entry for PO {purchase_order.id}: {e}", exc_info=True)
            return None

    @staticmethod
    def sync_bill_to_sales_ledger(bill):
        """
        Sync a bill to the sales ledger based on its status.
        Creates or removes ledger entries as needed.
        
        Args:
            bill: Bill instance to sync
        """
        from apps.cashandbank.models import AccountLedger
        
        if not bill.tenant:
            logger.warning(f"Bill {bill.id} has no tenant, skipping ledger sync")
            return None
        
        try:
            with transaction.atomic():
                # Check if this bill already has a ledger entry
                existing_entry = AccountLedger.objects.filter(
                    reference_type='bill',
                    reference_id=str(bill.id),
                    ledger_type='sales'
                ).first()
                
                # Determine if we should have a ledger entry
                should_have_entry = bill.status in ['paid', 'credit_sale']
                
                if should_have_entry:
                    if existing_entry:
                        # Entry already exists, skip
                        logger.info(f"Bill {bill.id} already has sales ledger entry")
                        return existing_entry
                    else:
                        # Create new entry
                        return LedgerService.create_sales_ledger_entry(bill)
                else:
                    # Bill status doesn't warrant a ledger entry
                    if existing_entry:
                        # Remove the ledger entry if it exists
                        existing_entry.delete()
                        logger.info(f"Removed sales ledger entry for bill {bill.id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error syncing bill {bill.id} to sales ledger: {e}", exc_info=True)
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
        
        if not purchase_order.tenant:
            logger.warning(f"Purchase Order {purchase_order.id} has no tenant, skipping ledger sync")
            return None
        
        try:
            with transaction.atomic():
                # Check if this PO already has a ledger entry
                existing_entry = AccountLedger.objects.filter(
                    reference_type='purchase_order',
                    reference_id=str(purchase_order.id),
                    ledger_type='purchase'
                ).first()
                
                # Determine if we should have a ledger entry (only when received or billed)
                should_have_entry = purchase_order.status in ['received', 'billed']
                
                if should_have_entry:
                    if existing_entry:
                        # Entry already exists, skip
                        logger.info(f"Purchase Order {purchase_order.id} already has purchase ledger entry")
                        return existing_entry
                    else:
                        # Create new entry
                        return LedgerService.create_purchase_ledger_entry(purchase_order)
                else:
                    # PO status doesn't warrant a ledger entry
                    if existing_entry:
                        # Remove the ledger entry if it exists
                        existing_entry.delete()
                        logger.info(f"Removed purchase ledger entry for PO {purchase_order.id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error syncing PO {purchase_order.id} to purchase ledger: {e}", exc_info=True)
            return None
