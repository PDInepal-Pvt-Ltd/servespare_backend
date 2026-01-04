from datetime import date
from decimal import Decimal
import uuid

from django.test import TestCase

from apps.branch.models import Branch
from apps.cashandbank.models import AccountLedger
from apps.stock_management.models import PurchaseOrder, PurchaseOrderItem, Party
from apps.tenant.models import Tenant


class PurchaseLedgerSignalTests(TestCase):
    """Verify purchase orders sync to the purchase ledger."""

    def setUp(self):
        self.tenant = Tenant.objects.create(
            business_name='Test Business',
            email='tenant@example.com',
        )
        self.branch = Branch.objects.create(
            tenant=self.tenant,
            branch_name='Main Branch',
            branch_code='MB001',
            Email='branch@example.com',
        )
        self.supplier = Party.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            party_type='supplier',
            party_name='Supplier One',
        )

    def _create_purchase_order(self):
        po = PurchaseOrder.objects.create(
            tenant=self.tenant,
            po_number=f'PO-{uuid.uuid4().hex[:8]}',
            status='draft',
            supplier=self.supplier,
            branch=self.branch,
            order_date=date.today(),
            expected_delivery_date=date.today(),
        )

        PurchaseOrderItem.objects.create(
            tenant=self.tenant,
            purchase_order=po,
            item_name='Brake Pad',
            quantity=Decimal('2.00'),
            unit_price=Decimal('50.00'),
            tax=Decimal('10.00'),
            branch=self.branch,
        )
        return po

    def test_purchase_order_creates_purchase_ledger_entry(self):
        po = self._create_purchase_order()

        po.status = 'received'
        po.save()

        ledger_entry = AccountLedger.objects.filter(
            reference_type='purchase_order',
            reference_id=str(po.id),
            ledger_type='purchase',
        ).first()

        self.assertIsNotNone(ledger_entry)
        self.assertEqual(ledger_entry.transaction_type, 'purchase')
        self.assertEqual(ledger_entry.credit, Decimal('110.00'))
        self.assertEqual(ledger_entry.debit, Decimal('0.00'))
        self.assertEqual(ledger_entry.branch, self.branch)

    def test_purchase_ledger_entry_removed_when_status_reverted(self):
        po = self._create_purchase_order()

        po.status = 'received'
        po.save()
        self.assertTrue(
            AccountLedger.objects.filter(
                reference_type='purchase_order',
                reference_id=str(po.id),
                ledger_type='purchase',
            ).exists()
        )

        po.status = 'draft'
        po.save()

        self.assertFalse(
            AccountLedger.objects.filter(
                reference_type='purchase_order',
                reference_id=str(po.id),
                ledger_type='purchase',
            ).exists()
        )
