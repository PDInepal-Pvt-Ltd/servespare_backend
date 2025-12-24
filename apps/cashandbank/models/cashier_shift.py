from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class CashierShift(BaseModel):
    """
    Represents a cashier's shift with opening/closing amounts and transactions.
    
    A shift tracks:
    - Opening float (amount at start of shift)
    - Expected balance (opening + sales - cash_out + adjustments)
    - Actual closing amount (counted at end of shift)
    - Variance (difference between expected and actual)
    """

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('flagged', 'Flagged'),
        ('transferred', 'Transferred'),
    ]

    # Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cashier_shifts',
        help_text='Tenant that owns this shift'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cashier_shifts',
        help_text='Branch where this shift occurred'
    )

    cashier = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='cashier_shifts',
        help_text='Cashier conducting this shift'
    )

    # Shift Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text='Status of the shift: open, closed, or flagged'
    )

    # Opening
    opening_float = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Cash amount at start of shift'
    )

    opened_at = models.DateTimeField(
        default=timezone.now,
        help_text='Timestamp when shift was opened'
    )

    # Running balances during shift
    expected_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Expected cash amount (opening + sales - adjustments)'
    )

    actual_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Actual counted cash amount at close'
    )

    # Closing
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when shift was closed'
    )

    # Variance tracking
    variance_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Difference between expected and actual (can be negative)'
    )

    variance_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for variance if closing amount differs from expected'
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text='General notes about the shift'
    )

    is_flagged = models.BooleanField(
        default=False,
        help_text='Auto-flagged if variance exceeds threshold (e.g., >100)'
    )


    # Transfer tracking
    transferred_to = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Name of the person/cashier this shift was transferred to'
    )

    transferred_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when shift was transferred'
    )

    transferred_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shifts_transferred_from',
        help_text='User who performed the transfer'
    )

    objects = TenantManager()

    class Meta:
        db_table = 'cashier_shift'
        verbose_name = 'Cashier Shift'
        verbose_name_plural = 'Cashier Shifts'
        ordering = ['-opened_at']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
            models.Index(fields=['cashier']),
            models.Index(fields=['status']),
            models.Index(fields=['opened_at']),
            models.Index(fields=['is_flagged']),
                models.Index(fields=['transferred_to']),
        ]

    def __str__(self):
        cashier_name = self.cashier.username if self.cashier else 'Unknown'
        return f"Shift {self.id} - {cashier_name} ({self.status}) on {self.opened_at:%Y-%m-%d}"

    def clean(self):
        """Validate shift state"""
        if self.status == 'open':
            if self.actual_amount is not None:
                raise ValidationError({'actual_amount': 'Actual amount should be None for open shifts'})
            if self.closed_at is not None:
                raise ValidationError({'closed_at': 'Closed timestamp should be None for open shifts'})
        
        if self.status == 'closed':
            if self.actual_amount is None:
                raise ValidationError({'actual_amount': 'Actual amount is required to close shift'})
            if self.closed_at is None:
                raise ValidationError({'closed_at': 'Closed timestamp is required to close shift'})

    @property
    def duration(self):
        """Return shift duration in minutes"""
        end_time = self.closed_at or timezone.now()
        delta = end_time - self.opened_at
        return delta.total_seconds() / 60

    @property
    def is_balanced(self):
        """Check if shift is balanced (within tolerance)"""
        if self.status != 'closed' or self.variance_amount is None:
            return None
        return abs(self.variance_amount) <= Decimal('0.01')

    def open_shift(self, opening_float):
        """
        Initialize and open a new shift.
        
        Args:
            opening_float: Decimal amount of opening cash
            
        Raises:
            ValidationError if opening_float is invalid
        """
        if opening_float is None or opening_float < 0:
            raise ValidationError('Opening float must be a non-negative value')
        
        self.status = 'open'
        self.opening_float = Decimal(str(opening_float))
        self.expected_amount = Decimal(str(opening_float))
        self.opened_at = timezone.now()
        self.save()

    def adjust_expected_amount(self, amount):
        """
        Adjust expected amount by amount (positive or negative).
        
        Args:
            amount: Decimal amount to adjust by
        """
        if self.status != 'open':
            raise ValidationError('Can only adjust expected amount on open shifts')
        
        self.expected_amount = (self.expected_amount or Decimal('0.00')) + Decimal(str(amount))
        self.save(update_fields=['expected_amount'])

    def close_shift(self, actual_amount, variance_reason=None, notes=None):
        """
        Close shift with actual counted amount.
        
        Args:
            actual_amount: Decimal actual cash counted
            variance_reason: Required reason if variance occurs
            notes: Optional notes
            
        Raises:
            ValidationError if shift is not open or amounts are invalid
        """
        if self.status != 'open':
            raise ValidationError('Can only close open shifts')
        
        if actual_amount is None or actual_amount < 0:
            raise ValidationError('Actual amount must be non-negative')
        
        actual_amount = Decimal(str(actual_amount))
        self.actual_amount = actual_amount
        self.variance_amount = actual_amount - (self.expected_amount or Decimal('0.00'))
        
        # Require variance_reason if there's any variance
        if abs(self.variance_amount) > Decimal('0.01') and not variance_reason:
            raise ValidationError('Variance reason is required when actual amount differs from expected')
        
        self.status = 'closed'
        self.closed_at = timezone.now()
        
        if notes:
            self.notes = notes
        
        if variance_reason:
            self.variance_reason = variance_reason
        
        # Auto-flag if variance exceeds threshold
        if abs(self.variance_amount) > Decimal('100.00'):
            self.is_flagged = True
        
        self.save()

    def get_transaction_summary(self):
        """Get summary of all transactions in this shift"""
        from apps.cashandbank.models.shift_transaction import ShiftTransaction
        
        transactions = self.shift_transactions.all()
        summary = {
            'total_cash_in': Decimal('0.00'),
            'total_cash_out': Decimal('0.00'),
            'total_sales': Decimal('0.00'),
            'total_adjustments': Decimal('0.00'),
            'transaction_count': 0,
        }
        
        for txn in transactions:
            if txn.transaction_type == 'opening':
                pass  # Already accounted in opening_float
            elif txn.transaction_type == 'cash_in':
                summary['total_cash_in'] += txn.amount
                summary['total_adjustments'] += txn.amount
            elif txn.transaction_type == 'cash_out':
                summary['total_cash_out'] += txn.amount
                summary['total_adjustments'] -= txn.amount
            elif txn.transaction_type == 'sale':
                summary['total_sales'] += txn.amount
            
            summary['transaction_count'] += 1
        
        return summary

    def transfer_shift(self, counted_cash, transferred_to, transferred_by=None, variance_reason=None):
        """
        Transfer shift to another cashier.

        Args:
            counted_cash: Decimal amount of cash counted
            transferred_to: Name of target cashier
            transferred_by: User performing the transfer
            variance_reason: Optional reason for variance if mismatch

        Raises:
            ValidationError if shift is not open or amounts are invalid
        """
        if self.status != 'open':
            raise ValidationError('Can only transfer open shifts')

        if not transferred_to or transferred_to.strip() == '':
            raise ValidationError('Target name is required for transfer')

        if counted_cash is None or counted_cash <= 0:
            raise ValidationError('Counted cash must be greater than zero')

        counted_cash = Decimal(str(counted_cash))

        # Compute variance
        expected = self.expected_amount or Decimal('0.00')
        variance = counted_cash - expected

        # Require reason when there is variance
        if variance != Decimal('0.00') and not variance_reason:
            raise ValidationError('Variance reason is required when counted cash differs from expected')

        # Update shift
        self.actual_amount = counted_cash
        self.variance_amount = variance
        self.status = 'transferred'
        self.transferred_to = transferred_to.strip()
        self.transferred_at = timezone.now()
        self.transferred_by = transferred_by
        self.closed_at = timezone.now()  # Set closed_at on transfer

        if variance_reason:
            self.variance_reason = variance_reason

        # Auto-flag if variance exceeds threshold
        if abs(variance) > Decimal('100.00'):
            self.is_flagged = True

        self.save()

    def compute_expected_amount(self):
        """
        Compute expected amount from opening float and all transactions.

        Formula: expected = opening_float + sales + cash_in - cash_out

        Returns:
            Decimal expected amount
        """
        from apps.cashandbank.models.shift_transaction import ShiftTransaction

        expected = self.opening_float or Decimal('0.00')

        transactions = self.shift_transactions.exclude(transaction_type='opening').exclude(transaction_type='closing')

        for txn in transactions:
            if txn.transaction_type in ('cash_in', 'sale'):
                expected += txn.amount
            elif txn.transaction_type == 'cash_out':
                expected -= txn.amount

        return expected

    def compute_variance(self, counted_cash):
        """
        Compute variance between counted cash and expected amount.

        Args:
            counted_cash: Decimal amount counted
        
        Returns:
            Decimal variance (counted_cash - expected)
        """
        expected = self.expected_amount or Decimal('0.00')
        return counted_cash - expected
