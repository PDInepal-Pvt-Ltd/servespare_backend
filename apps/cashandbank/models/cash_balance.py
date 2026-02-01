from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class CashBalance(BaseModel):
    """Tenant+Branch level cash balance.

    Maintains a running balance for a tenant and branch. Use select_for_update
    when mutating to avoid races.
    """
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cash_balances',
        help_text='Tenant that owns this balance'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='cash_balances',
        help_text='Branch for this cash balance'
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Current cash balance for the tenant+branch'
    )

    last_updated = models.DateTimeField(default=timezone.now)

    objects = TenantManager()

    class Meta:
        db_table = 'cash_balance'
        verbose_name = 'Cash Balance'
        verbose_name_plural = 'Cash Balances'
        ordering = ['-last_updated']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]

    def __str__(self):
        t = self.tenant and f"Tenant:{self.tenant.id}" or 'Global'
        b = self.branch and f"Branch:{self.branch.id}" or 'NoBranch'
        return f"{t} {b} Balance: {self.balance}"

    def clean(self):
        errors = {}

        if self.balance is not None and self.balance < Decimal('0.00'):
            errors['balance'] = 'Balance cannot be negative.'

        if not self.last_updated:
            errors['last_updated'] = 'Last updated timestamp is required.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def adjust(self, amount):
        """Adjust the balance by `amount` (Decimal). Positive to add, negative to subtract."""
        self.balance = (self.balance or Decimal('0.00')) + Decimal(amount)
        self.last_updated = timezone.now()
        self.save(update_fields=['balance', 'last_updated'])
