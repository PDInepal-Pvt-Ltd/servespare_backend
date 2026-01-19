from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class BankTransfer(BaseModel):
    """Represents a transfer from tenant+branch cash balance into a bank account."""

    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bank_transfers',
        help_text='Tenant that owns this transfer'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_transfers',
        help_text='Branch from which cash is deducted'
    )

    bank_account = models.ForeignKey(
        'cashandbank.BankAccount',
        on_delete=models.PROTECT,
        related_name='bank_transfers',
        help_text='Destination bank account for this transfer'
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Amount transferred'
    )

    description = models.TextField(blank=True, null=True)

    transfer_date = models.DateTimeField(default=timezone.now)

    objects = TenantManager()

    class Meta:
        db_table = 'bank_transfer'
        verbose_name = 'Bank Transfer'
        verbose_name_plural = 'Bank Transfers'
        ordering = ['-transfer_date']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
            models.Index(fields=['bank_account']),
        ]

    def __str__(self):
        return f"BankTransfer {self.amount} -> {self.bank_account} on {self.transfer_date:%Y-%m-%d}"

    def save(self, *args, **kwargs):
        """On create, atomically deduct tenant+branch CashBalance and credit BankAccount.balance.

        Use select_for_update to avoid races.
        """
        from apps.cashandbank.models.cash_balance import CashBalance
        from apps.cashandbank.models.bank_accounts import BankAccount

        self.full_clean()
        is_create = self._state.adding

        if not is_create:
            # For updates, do default save (no balance re-adjustment)
            return super().save(*args, **kwargs)

        with transaction.atomic():
            # Lock or create cash balance row for tenant+branch
            cb, _ = CashBalance.objects.select_for_update().get_or_create(
                tenant=self.tenant,
                branch=self.branch,
                defaults={'balance': Decimal('0.00')}
            )

            # Lock bank account row
            ba = BankAccount.objects.select_for_update().get(pk=self.bank_account_id)

            # Adjust balances
            cb.balance = (cb.balance or Decimal('0.00')) - Decimal(self.amount)
            cb.last_updated = timezone.now()
            cb.save(update_fields=['balance', 'last_updated'])

            ba.balance = (ba.balance or Decimal('0.00')) + Decimal(self.amount)
            ba.save(update_fields=['balance'])

            # Finally save the transfer record
            super().save(*args, **kwargs)

    def clean(self):
        errors = {}

        if not self.bank_account_id and not self.bank_account:
            errors['bank_account'] = 'Bank account is required.'

        if self.amount is None:
            errors['amount'] = 'Amount is required.'
        elif self.amount <= 0:
            errors['amount'] = 'Amount must be greater than zero.'

        if self.description and len(self.description.strip()) > 500:
            errors['description'] = 'Description cannot exceed 500 characters.'

        if not self.transfer_date:
            errors['transfer_date'] = 'Transfer date is required.'

        if errors:
            raise ValidationError(errors)
