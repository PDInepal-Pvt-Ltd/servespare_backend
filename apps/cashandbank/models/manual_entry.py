from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class ManualEntry(BaseModel):
    TYPE_CHOICES = [
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
    ]

    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='manual_entries',
        help_text='Tenant that owns this manual entry'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='manual_entries',
        help_text='Branch associated with this manual entry'
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text='cash_in or cash_out'
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Amount for this manual entry'
    )

    description = models.TextField(blank=True, null=True)

    entry_date = models.DateTimeField(default=timezone.now)

    objects = TenantManager()

    class Meta:
        db_table = 'manual_entry'
        verbose_name = 'Manual Entry'
        verbose_name_plural = 'Manual Entries'
        ordering = ['-entry_date']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.amount} ({self.entry_date:%Y-%m-%d})"

    def save(self, *args, **kwargs):
        """On create, update the CashBalance for tenant+branch atomically.

        - `cash_in`: increases balance
        - `cash_out`: decreases balance
        """
        from apps.cashandbank.models.cash_balance import CashBalance

        is_create = self._state.adding

        self.full_clean()

        with transaction.atomic():
            super().save(*args, **kwargs)

            if is_create:
                # Lock or create the cash balance row
                cb, _ = CashBalance.objects.select_for_update().get_or_create(
                    tenant=self.tenant,
                    branch=self.branch,
                    defaults={'balance': Decimal('0.00')}
                )

                if self.transaction_type == 'cash_in':
                    cb.balance = (cb.balance or Decimal('0.00')) + Decimal(self.amount)
                else:
                    # cash_out
                    cb.balance = (cb.balance or Decimal('0.00')) - Decimal(self.amount)

                cb.last_updated = timezone.now()
                cb.save(update_fields=['balance', 'last_updated'])

    def clean(self):
        errors = {}

        if not self.transaction_type:
            errors['transaction_type'] = 'Transaction type is required.'
        elif self.transaction_type not in dict(self.TYPE_CHOICES):
            errors['transaction_type'] = 'Invalid transaction type.'

        if self.amount is None:
            errors['amount'] = 'Amount is required.'
        elif self.amount <= 0:
            errors['amount'] = 'Amount must be greater than zero.'

        if self.description and len(self.description.strip()) > 1000:
            errors['description'] = 'Description cannot exceed 1000 characters.'

        if not self.entry_date:
            errors['entry_date'] = 'Entry date is required.'

        if errors:
            raise ValidationError(errors)
