from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class ShiftTransaction(BaseModel):
    """
    Represents individual transactions within a cashier shift.
    
    Types:
    - opening: Initial float when shift opens
    - cash_in: Manual cash addition (e.g., customer payment, refund)
    - cash_out: Manual cash removal (e.g., reimbursement)
    - sale: Auto-posted from bill creation (payment method = cash)
    - closing: Final count when shift closes
    """

    TYPE_CHOICES = [
        ('opening', 'Opening'),
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('sale', 'Sale'),
        ('closing', 'Closing'),
    ]

    # Shift reference
    shift = models.ForeignKey(
        'cashandbank.CashierShift',
        on_delete=models.CASCADE,
        related_name='shift_transactions',
        help_text='Shift this transaction belongs to'
    )

    # Tenant context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shift_transactions',
        help_text='Tenant that owns this transaction'
    )

    # Transaction type and amount
    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text='Type of transaction'
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Amount involved in transaction'
    )

    # Description
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Description or reason for transaction'
    )

    # Source reference (optional)
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Type of reference (e.g., bill, invoice)'
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
        help_text='When this transaction occurred'
    )

    # User who performed the transaction
    performed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shift_transactions',
        help_text='User who performed this transaction'
    )

    objects = TenantManager()

    class Meta:
        db_table = 'shift_transaction'
        verbose_name = 'Shift Transaction'
        verbose_name_plural = 'Shift Transactions'
        ordering = ['transaction_date']
        indexes = [
            models.Index(fields=['shift']),
            models.Index(fields=['tenant']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} on {self.transaction_date:%Y-%m-%d %H:%M}"

    @property
    def signed_amount(self):
        """Return amount with appropriate sign"""
        if self.transaction_type in ('cash_in', 'sale', 'opening'):
            return self.amount
        else:  # cash_out, closing
            return -self.amount

    def save(self, *args, **kwargs):
        """On create, update the CashBalance for tenant+branch atomically.

        - `opening`: increases balance
        - `cash_in`: increases balance
        - `sale`: increases balance
        - `cash_out`: decreases balance
        - `closing`: no effect (final count, doesn't change balance)
        """
        from apps.cashandbank.models.cash_balance import CashBalance

        self.full_clean()
        is_create = self._state.adding

        # Validate that shift is open when creating non-opening/closing transactions
        if is_create and self.shift:
            # Only allow opening transactions when shift is in any state (initial open)
            # Allow closing transactions when shift is open (about to close)
            # For all other transaction types, shift must be open
            if self.transaction_type not in ('opening', 'closing'):
                if self.shift.status != 'open':
                    raise ValidationError(
                        f'Cannot create {self.get_transaction_type_display()} transaction. '
                        f'Shift must be open to perform this transaction.'
                    )

        with transaction.atomic():
            super().save(*args, **kwargs)

            if is_create:
                # Get shift to access branch
                shift = self.shift
                branch = shift.branch if shift else None

                # Only update balance for relevant transaction types
                # closing transactions don't affect the balance
                if self.transaction_type in ('opening', 'cash_in', 'sale', 'cash_out'):
                    # Lock or create the cash balance row
                    cb, _ = CashBalance.objects.select_for_update().get_or_create(
                        tenant=self.tenant,
                        branch=branch,
                        defaults={'balance': Decimal('0.00')}
                    )

                    if self.transaction_type in ('opening', 'cash_in', 'sale'):
                        cb.balance = (cb.balance or Decimal('0.00')) + Decimal(self.amount)
                    elif self.transaction_type == 'cash_out':
                        cb.balance = (cb.balance or Decimal('0.00')) - Decimal(self.amount)

                    cb.last_updated = timezone.now()
                    cb.save(update_fields=['balance', 'last_updated'])

    def clean(self):
        errors = {}

        if not self.shift_id and not self.shift:
            errors['shift'] = 'Shift is required.'

        if not self.transaction_type:
            errors['transaction_type'] = 'Transaction type is required.'
        elif self.transaction_type not in dict(self.TYPE_CHOICES):
            errors['transaction_type'] = 'Invalid transaction type.'

        if self.amount is None:
            errors['amount'] = 'Amount is required.'
        elif self.amount < 0:
            errors['amount'] = 'Amount cannot be negative.'

        if self.description and len(self.description.strip()) > 2000:
            errors['description'] = 'Description cannot exceed 2000 characters.'

        if self.reference_type and len(self.reference_type.strip()) > 50:
            errors['reference_type'] = 'Reference type cannot exceed 50 characters.'

        if self.reference_id and len(self.reference_id.strip()) > 100:
            errors['reference_id'] = 'Reference ID cannot exceed 100 characters.'

        if not self.transaction_date:
            errors['transaction_date'] = 'Transaction date is required.'

        if errors:
            raise ValidationError(errors)
