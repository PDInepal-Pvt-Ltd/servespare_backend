from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.tenant.models import Tenant
from apps.branch.models import Branch
from apps.cashandbank.models import CashierShift, ShiftTransaction

User = get_user_model()


class ShiftTransactionValidationTestCase(TestCase):
    """Test that shift transactions can only be created when shift is open"""

    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(
            business_name="Test Tenant",
            email="test@tenant.com"
        )

        # Create branch
        self.branch = Branch.objects.create(
            branch_name="Test Branch",
            branch_code="TB001",
            Email="branch@test.com",
            tenant=self.tenant
        )

        # Create user
        self.user = User.objects.create_user(
            username="testcashier",
            email="cashier@test.com",
            password="testpass123",
            tenant=self.tenant
        )

    def test_cash_in_transaction_requires_open_shift(self):
        """Test that cash_in transactions require the shift to be open"""
        # Create a closed shift
        shift = CashierShift.objects.create(
            cashier=self.user,
            branch=self.branch,
            tenant=self.tenant,
            opening_float=Decimal('1000.00'),
            status='closed'
        )

        # Try to create a cash_in transaction on closed shift
        with self.assertRaises(ValidationError) as context:
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=self.tenant,
                transaction_type='cash_in',
                amount=Decimal('100.00'),
                description='Test cash in',
                performed_by=self.user
            )

        self.assertIn('Shift must be open', str(context.exception))

    def test_cash_out_transaction_requires_open_shift(self):
        """Test that cash_out transactions require the shift to be open"""
        # Create a closed shift
        shift = CashierShift.objects.create(
            cashier=self.user,
            branch=self.branch,
            tenant=self.tenant,
            opening_float=Decimal('1000.00'),
            status='closed'
        )

        # Try to create a cash_out transaction on closed shift
        with self.assertRaises(ValidationError) as context:
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=self.tenant,
                transaction_type='cash_out',
                amount=Decimal('50.00'),
                description='Test cash out',
                performed_by=self.user
            )

        self.assertIn('Shift must be open', str(context.exception))

    def test_sale_transaction_requires_open_shift(self):
        """Test that sale transactions require the shift to be open"""
        # Create a closed shift
        shift = CashierShift.objects.create(
            cashier=self.user,
            branch=self.branch,
            tenant=self.tenant,
            opening_float=Decimal('1000.00'),
            status='closed'
        )

        # Try to create a sale transaction on closed shift
        with self.assertRaises(ValidationError) as context:
            ShiftTransaction.objects.create(
                shift=shift,
                tenant=self.tenant,
                transaction_type='sale',
                amount=Decimal('200.00'),
                description='Test sale',
                performed_by=self.user
            )

        self.assertIn('Shift must be open', str(context.exception))

    def test_transactions_allowed_on_open_shift(self):
        """Test that transactions are allowed when shift is open"""
        # Create an open shift
        shift = CashierShift.objects.create(
            cashier=self.user,
            branch=self.branch,
            tenant=self.tenant,
            opening_float=Decimal('1000.00'),
            status='open'
        )

        # These should all succeed
        cash_in = ShiftTransaction.objects.create(
            shift=shift,
            tenant=self.tenant,
            transaction_type='cash_in',
            amount=Decimal('100.00'),
            description='Test cash in',
            performed_by=self.user
        )
        self.assertIsNotNone(cash_in.id)

        cash_out = ShiftTransaction.objects.create(
            shift=shift,
            tenant=self.tenant,
            transaction_type='cash_out',
            amount=Decimal('50.00'),
            description='Test cash out',
            performed_by=self.user
        )
        self.assertIsNotNone(cash_out.id)

        sale = ShiftTransaction.objects.create(
            shift=shift,
            tenant=self.tenant,
            transaction_type='sale',
            amount=Decimal('200.00'),
            description='Test sale',
            performed_by=self.user
        )
        self.assertIsNotNone(sale.id)

    def test_opening_transaction_allowed_on_any_status(self):
        """Test that opening transactions are allowed regardless of shift status"""
        # Create a shift with 'pending' status (before opening)
        shift = CashierShift.objects.create(
            cashier=self.user,
            branch=self.branch,
            tenant=self.tenant,
            opening_float=Decimal('1000.00'),
            status='pending'
        )

        # Opening transaction should be allowed
        opening = ShiftTransaction.objects.create(
            shift=shift,
            tenant=self.tenant,
            transaction_type='opening',
            amount=Decimal('1000.00'),
            description='Opening float',
            performed_by=self.user
        )
        self.assertIsNotNone(opening.id)

    def test_closing_transaction_allowed_on_any_status(self):
        """Test that closing transactions are allowed regardless of shift status"""
        # Create an open shift
        shift = CashierShift.objects.create(
            cashier=self.user,
            branch=self.branch,
            tenant=self.tenant,
            opening_float=Decimal('1000.00'),
            status='open'
        )

        # Closing transaction should be allowed
        closing = ShiftTransaction.objects.create(
            shift=shift,
            tenant=self.tenant,
            transaction_type='closing',
            amount=Decimal('1000.00'),
            description='Closing shift',
            performed_by=self.user
        )
        self.assertIsNotNone(closing.id)
