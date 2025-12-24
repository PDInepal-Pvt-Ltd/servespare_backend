"""
Test cases for Account Ledger functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.cashandbank.models import (
    AccountLedger,
    CashierShift,
    ShiftTransaction,
)
from apps.tenant.models import Tenant
from apps.branch.models import Branch

User = get_user_model()


class AccountLedgerTestCase(TestCase):
    """Test Account Ledger creation and functionality"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            contact_email='test@example.com'
        )

        # Create branch
        self.branch = Branch.objects.create(
            name='Test Branch',
            tenant=self.tenant
        )

        # Create user
        self.user = User.objects.create_user(
            username='testcashier',
            password='testpass123',
            tenant=self.tenant
        )

        # Create shift
        self.shift = CashierShift.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            cashier=self.user,
            opening_float=Decimal('1000.00'),
            status='open'
        )

    def test_account_ledger_creation(self):
        """Test manual account ledger entry creation"""
        ledger = AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='opening',
            debit=Decimal('1000.00'),
            credit=Decimal('0.00'),
            balance=Decimal('1000.00'),
            description='Shift Opening - Cash Float',
            reference=f'Shift #{self.shift.id}',
            reference_type='shift',
            reference_id=str(self.shift.id),
            performed_by=self.user,
            is_manual_entry=True
        )

        self.assertEqual(ledger.debit, Decimal('1000.00'))
        self.assertEqual(ledger.credit, Decimal('0.00'))
        self.assertEqual(ledger.balance, Decimal('1000.00'))
        self.assertEqual(ledger.ledger_type, 'general')
        self.assertEqual(ledger.transaction_type, 'opening')

    def test_ledger_auto_sync_from_shift_transaction(self):
        """Test automatic ledger creation from shift transaction"""
        # Create a shift transaction
        shift_txn = ShiftTransaction.objects.create(
            shift=self.shift,
            tenant=self.tenant,
            transaction_type='cash_in',
            amount=Decimal('500.00'),
            description='Cash In Test',
            performed_by=self.user
        )

        # Check if ledger entry was auto-created
        ledger_entries = AccountLedger.objects.filter(
            shift=self.shift,
            ledger_type='general'
        )

        self.assertTrue(ledger_entries.exists())
        
        # Verify at least one entry was created
        self.assertGreaterEqual(ledger_entries.count(), 1)

    def test_running_balance_calculation(self):
        """Test running balance is calculated correctly"""
        # Create multiple ledger entries
        AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='opening',
            debit=Decimal('100.00'),
            credit=Decimal('0.00'),
            balance=Decimal('100.00'),
            description='Opening',
            performed_by=self.user
        )

        AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='cash_in',
            debit=Decimal('1000.00'),
            credit=Decimal('0.00'),
            balance=Decimal('1100.00'),  # 100 + 1000
            description='Cash In',
            performed_by=self.user
        )

        AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='cash_out',
            debit=Decimal('0.00'),
            credit=Decimal('500.00'),
            balance=Decimal('600.00'),  # 1100 - 500
            description='Cash Out',
            performed_by=self.user
        )

        # Verify balances
        entries = AccountLedger.objects.filter(
            shift=self.shift,
            ledger_type='general'
        ).order_by('transaction_date', 'id')

        balances = [entry.balance for entry in entries]
        expected = [Decimal('100.00'), Decimal('1100.00'), Decimal('600.00')]
        
        self.assertEqual(balances, expected)

    def test_ledger_types(self):
        """Test different ledger types are created correctly"""
        # Create sale transaction
        shift_txn = ShiftTransaction.objects.create(
            shift=self.shift,
            tenant=self.tenant,
            transaction_type='sale',
            amount=Decimal('500.00'),
            description='Sale Test',
            performed_by=self.user
        )

        # Should create entries in both general and sales ledgers
        general_entries = AccountLedger.objects.filter(
            shift=self.shift,
            ledger_type='general'
        )

        sales_entries = AccountLedger.objects.filter(
            shift=self.shift,
            ledger_type='sales'
        )

        self.assertTrue(general_entries.exists())
        self.assertTrue(sales_entries.exists())

    def test_ledger_summary_calculation(self):
        """Test summary calculations"""
        # Create test ledger entries
        AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='opening',
            debit=Decimal('100.00'),
            credit=Decimal('0.00'),
            balance=Decimal('100.00'),
            description='Opening',
            performed_by=self.user
        )

        AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='cash_in',
            debit=Decimal('1000.00'),
            credit=Decimal('0.00'),
            balance=Decimal('1100.00'),
            description='Cash In',
            performed_by=self.user
        )

        AccountLedger.objects.create(
            tenant=self.tenant,
            branch=self.branch,
            shift=self.shift,
            ledger_type='general',
            transaction_type='closing',
            debit=Decimal('0.00'),
            credit=Decimal('1000.00'),
            balance=Decimal('100.00'),
            description='Closing',
            performed_by=self.user
        )

        # Calculate summary
        entries = AccountLedger.objects.filter(
            shift=self.shift,
            ledger_type='general'
        )

        total_debit = sum(entry.debit for entry in entries)
        total_credit = sum(entry.credit for entry in entries)
        net_balance = total_debit - total_credit

        self.assertEqual(total_debit, Decimal('1100.00'))
        self.assertEqual(total_credit, Decimal('1000.00'))
        self.assertEqual(net_balance, Decimal('100.00'))

    def tearDown(self):
        """Clean up test data"""
        AccountLedger.objects.all().delete()
        ShiftTransaction.objects.all().delete()
        CashierShift.objects.all().delete()
        Branch.objects.all().delete()
        User.objects.all().delete()
        Tenant.objects.all().delete()
