"""
Management command to synchronize existing bills and purchase orders to their respective ledgers.

Usage:
    python manage.py sync_transactions_to_ledgers [--bills-only] [--pos-only] [--tenant TENANT_ID]
"""
from django.core.management.base import BaseCommand, CommandError
import logging

from apps.cashandbank.ledger_service import LedgerService
from apps.stock_management.models import PurchaseOrder

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
        bills_only = options['bills_only']
        pos_only = options['pos_only']
        tenant_id = options['tenant']
        dry_run = options['dry_run']

        if bills_only and pos_only:
            raise CommandError('Use either --bills-only or --pos-only, not both.')

        process_purchase_orders = not bills_only

        if process_purchase_orders:
            synced = skipped = failed = 0
            po_queryset = PurchaseOrder.objects.all().order_by('order_date', 'id')

            if tenant_id:
                po_queryset = po_queryset.filter(tenant_id=tenant_id)

            if not po_queryset.exists():
                self.stdout.write(self.style.WARNING('No purchase orders found to synchronize.'))
            else:
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"Synchronizing {po_queryset.count()} purchase orders" + (' [dry run]' if dry_run else '')
                    )
                )

            for po in po_queryset:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] PurchaseOrder {po.id} ({po.status}) would be synced to purchase ledger"
                    )
                    continue

                try:
                    LedgerService.sync_purchase_order_to_purchase_ledger(po)
                    if po.status in {'received', 'billed'}:
                        synced += 1
                    else:
                        skipped += 1
                except Exception as exc:
                    failed += 1
                    logger.exception("Error syncing PurchaseOrder %s: %s", po.id, exc)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Purchase orders synchronized: {synced} created/updated, {skipped} skipped, {failed} failed"
                )
            )

        if not pos_only:
            self.stdout.write(
                self.style.WARNING(
                    'Bill synchronization is not implemented in this command version; skipping bills.'
                )
            )
