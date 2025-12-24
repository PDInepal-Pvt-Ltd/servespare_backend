from django.db import models
from django.utils import timezone
from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class AccountLedger(BaseModel):
    """
    Complete financial record with running balance for a cashier shift.
    
    Ledger Types:
    - general: All transactions (cash in/out, sales, adjustments)
    - sales: Only sales-related transactions
    - purchase: Only purchase-related transactions (cash out for purchases)
    
    This model stores ledger entries with:
    - Transaction details (date, time, description, reference)
    - Debit/Credit amounts
    - Running balance calculation
    """

    LEDGER_TYPE_CHOICES = [
        ('general', 'General Ledger'),
        ('sales', 'Sales Ledger'),
        ('purchase', 'Purchase Ledger'),
        ('account', 'Account Ledger'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('opening', 'Shift Opening'),
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('closing', 'Shift Closing'),
        ('adjustment', 'Adjustment'),
        ('refund', 'Refund'),
    ]

    # Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='account_ledgers',
        help_text='Tenant that owns this ledger'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='account_ledgers',
        help_text='Branch this ledger belongs to'
    )

    shift = models.ForeignKey(
        'cashandbank.CashierShift',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='account_ledgers',
        help_text='Shift this ledger entry belongs to'
    )

    # Ledger type
    ledger_type = models.CharField(
        max_length=20,
        choices=LEDGER_TYPE_CHOICES,
        default='general',
        help_text='Type of ledger (general, sales, purchase, account)'
    )

    # Transaction type
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text='Type of transaction'
    )

    # Amounts
    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Debit amount (inflow/cash in)'
    )

    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Credit amount (outflow/cash out)'
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Running balance after this transaction'
    )

    # Description and reference
    description = models.TextField(
        help_text='Description of the transaction'
    )

    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Reference number (e.g., Shift #shift_17, Bill #123)'
    )

    reference_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Type of reference (shift, bill, invoice, etc.)'
    )

    reference_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='ID of referenced object'
    )

    # Timestamp
    transaction_date = models.DateTimeField(
        default=timezone.now,
        help_text='Date and time of transaction'
    )

    # User who performed the transaction
    performed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='account_ledger_entries',
        help_text='User who performed this transaction'
    )

    # Additional metadata
    is_manual_entry = models.BooleanField(
        default=False,
        help_text='Whether this was a manual entry'
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes'
    )

    objects = TenantManager()

    class Meta:
        db_table = 'account_ledger'
        verbose_name = 'Account Ledger'
        verbose_name_plural = 'Account Ledgers'
        ordering = ['transaction_date', 'id']
        indexes = [
            models.Index(fields=['shift']),
            models.Index(fields=['tenant']),
            models.Index(fields=['ledger_type']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['branch']),
            models.Index(fields=['tenant', 'shift', 'transaction_date']),
        ]

    def __str__(self):
        return f"{self.get_ledger_type_display()} - {self.description} ({self.transaction_date:%Y-%m-%d %H:%M})"

    @property
    def total_inflow(self):
        """Total debit amount"""
        return self.debit

    @property
    def total_outflow(self):
        """Total credit amount"""
        return self.credit

    @property
    def net_amount(self):
        """Net amount (debit - credit)"""
        return self.debit - self.credit
    class Meta:
        indexes = [
            models.Index(fields=['shift', 'ledger_type']),
            models.Index(fields=['tenant', 'branch']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['ledger_type']),
        ]


class SalesLedger(AccountLedger):
    """
    Proxy model for Sales Ledger entries.
    Filters AccountLedger to show only sales-related transactions.
    """
    class Meta:
        proxy = True
        verbose_name = 'Sales Ledger'
        verbose_name_plural = 'Sales Ledgers'


class PurchaseLedger(AccountLedger):
    """
    Proxy model for Purchase Ledger entries.
    Filters AccountLedger to show only purchase-related transactions.
    """
    class Meta:
        proxy = True
        verbose_name = 'Purchase Ledger'
        verbose_name_plural = 'Purchase Ledgers'