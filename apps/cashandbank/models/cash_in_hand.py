from django.db import models
from django.db.models import Sum, F, Case, When, DecimalField
from django.utils import timezone

from apps.base.models import BaseModel
from apps.base.managers import TenantManager, TenantQuerySet
from apps.cashandbank.models.bank_accounts import BankAccount


class CashTransactionQuerySet(TenantQuerySet):
    def with_signed_amount(self):
        return self.annotate(
            signed_amount=Case(
                When(transaction_type='cash_in', then=F('amount')),
                default=-F('amount'),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )

    def total_balance(self):
        agg = self.with_signed_amount().aggregate(total=Sum('signed_amount'))
        return agg.get('total') or 0


class CashTransactionManager(TenantManager):
    """Manager that keeps tenant scoping while exposing custom queryset helpers."""

    def get_queryset(self):
        qs = CashTransactionQuerySet(self.model, using=self._db)
        return qs._maybe_filter()


class CashTransaction(BaseModel):
    """
    Cash transaction ledger for cash in, cash out, and transfers.

    Fields exposed for listing:
    - id (Transaction ID)
    - transaction_type (cash_in, cash_out, transfer)
    - source_description
    - amount
    - transaction_date

    Total balance rule: cash_in adds, cash_out and transfer subtract.
    """

    TYPE_CHOICES = [
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('transfer', 'Transfer'),
    ]

    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cash_transactions',
        help_text='Tenant that owns this cash transaction'
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text='Type of transaction: cash_in, cash_out, transfer'
    )

    source_description = models.TextField(
        blank=True,
        null=True,
        help_text='Source or description of the transaction'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Absolute amount of the transaction'
    )

    transaction_date = models.DateTimeField(
        default=timezone.now,
        help_text='Date and time of the transaction'
    )

    # Optional references for transfers (and cash account mapping if used)
    from_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cash_transactions_from',
        help_text='Source account for transfer (optional)'
    )

    to_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cash_transactions_to',
        help_text='Destination account for transfer (optional)'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_transactions',
        help_text='Branch associated with this cash transaction'
    )

    objects = CashTransactionManager()

    class Meta:
        db_table = 'cash_transaction'
        verbose_name = 'Cash Transaction'
        verbose_name_plural = 'Cash Transactions'
        ordering = ['-transaction_date', '-created']
        indexes = [
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} on {self.transaction_date:%Y-%m-%d}"

    @property
    def signed_amount(self):
        """Return amount with sign rule (in = +, out/transfer = -)."""
        if self.transaction_type == 'cash_in':
            return self.amount
        return -self.amount

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.amount is None or self.amount < 0:
            raise ValidationError({'amount': 'Amount must be a non-negative value.'})
