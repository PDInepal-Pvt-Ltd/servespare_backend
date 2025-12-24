"""
Management command to synchronize existing bills and purchase orders to their respective ledgers.

Usage:
    python manage.py sync_transactions_to_ledgers [--bills-only] [--pos-only] [--tenant TENANT_ID]
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronize existing bills and purchase orders to their respective ledgers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bills-only',
            action='store_true',
            help='Sync only bills to sales ledger',
        )
        parser.add_argument(
            '--pos-only',
            action='store_true',
            help='Sync only purchase orders to purchase ledger',
        )
        parser.add_argument(
            '--tenant',
            type=int,
            help='Sync only for specific tenant ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        from apps.cashandbank.ledger_service import LedgerService
        from apps.sales.models import Bill
        from apps.stock_management.models import PurchaseOrder
        from apps.cashandbank.models import AccountLedger

        bills_only = options.get('bills_only')
        pos_only = options.get('pos_only')
        tenant_id = options.get('tenant')
        dry_run = options.get('dry_run')

        # Default to both if neither is specified
        if not bills_only and not pos_only:
            bills_only = True
            pos_only = True

        bill_count = 0
        po_count = 0

        # Sync Bills to Sales Ledger
        if bills_only or (bills_only and pos_only):
            self.stdout.write(self.style.SUCCESS('Syncing Bills to Sales Ledger...'))
            
            bills_query = Bill.objects.filter(status__in=['paid', 'credit_sale'])
            if tenant_id:
                bills_query = bills_query.filter(tenant_id=tenant_id)
            
            # Exclude bills that already have ledger entries
            bills_without_ledger = []
            for bill in bills_query:
                existing = AccountLedger.objects.filter(
                    reference_type='bill',
                    reference_id=str(bill.id),
                    ledger_type='sales'
                ).exists()
                if not existing:
                    bills_without_ledger.append(bill)
            
            for bill in bills_without_ledger:
                try:
                    if dry_run:
                        total = bill.total_after_discount or Decimal('0.00')
                        self.stdout.write(
                            f"  [DRY RUN] Would sync Bill #{bill.id} "
                            f"({bill.customer_name}) - Amount: {total}"
                        )
                    else:
                        ledger = LedgerService.create_sales_ledger_entry(bill)
                        if ledger:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Synced Bill #{bill.id} "
                                    f"({bill.customer_name}) - Ledger ID: {ledger.id}"
                                )
                            )
                            bill_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Error syncing Bill #{bill.id}: {e}")
                    )

        # Sync Purchase Orders to Purchase Ledger
        if pos_only or (bills_only and pos_only):
            self.stdout.write(self.style.SUCCESS('\nSyncing Purchase Orders to Purchase Ledger...'))
            
            pos_query = PurchaseOrder.objects.filter(status__in=['received', 'billed'])
            if tenant_id:
                pos_query = pos_query.filter(tenant_id=tenant_id)
            
            # Exclude POs that already have ledger entries
            pos_without_ledger = []
            for po in pos_query:
                existing = AccountLedger.objects.filter(
                    reference_type='purchase_order',
                    reference_id=str(po.id),
                    ledger_type='purchase'
                ).exists()
                if not existing:
                    pos_without_ledger.append(po)
            
            for po in pos_without_ledger:
                try:
                    if dry_run:
                        total = po.total_amount or Decimal('0.00')
                        self.stdout.write(
                            f"  [DRY RUN] Would sync PO #{po.po_number} "
                            f"({po.supplier.party_name}) - Amount: {total}"
                        )
                    else:
                        ledger = LedgerService.create_purchase_ledger_entry(po)
                        if ledger:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ✓ Synced PO #{po.po_number} "
                                    f"({po.supplier.party_name}) - Ledger ID: {ledger.id}"
                                )
                            )
                            po_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Error syncing PO #{po.po_number}: {e}")
                    )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN COMPLETED:\n'
                    f'  Would sync {len(bills_without_ledger) if bills_only or (bills_only and pos_only) else 0} bills\n'
                    f'  Would sync {len(pos_without_ledger) if pos_only or (bills_only and pos_only) else 0} purchase orders'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'SYNC COMPLETED:\n'
                    f'  Synced {bill_count} bills to sales ledger\n'
                    f'  Synced {po_count} purchase orders to purchase ledger'
                )
            )
