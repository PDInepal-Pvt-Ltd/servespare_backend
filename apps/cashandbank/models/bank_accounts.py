from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class BankAccount(BaseModel):
    """
    Model to store bank account information
    """
    ACCOUNT_TYPE_CHOICES = [
        ('bank_account', 'Bank Account'),
        ('esewa', 'eSewa'),
        ('fonepay', 'FonePay'),
        ('cash', 'Cash'),
    ]
    
    # Account Type
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        help_text='Type of account: Bank Account, eSewa, FonePay, or Cash'
    )
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bank_accounts',
        help_text='Tenant that owns this bank account'
    )

    # Account Information
    account_name = models.CharField(
        max_length=255,
        help_text='Name of the account'
    )
    
    bank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Name of the bank (required for bank accounts)'
    )
    
    account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Account number or identifier'
    )
    
    account_holders_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Name of the account holder'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_accounts',
        help_text='Branch associated with this bank account'
    )
    
    # Running balance for the account (tenant+branch scoped)
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text='Current balance for this bank account'
    )
    
    class Meta:
        db_table = 'bank_account'
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        ordering = ['account_name']
        indexes = [
            models.Index(fields=['account_type']),
            models.Index(fields=['account_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]
    
    def __str__(self):
        account_type_display = self.get_account_type_display()
        return f"{self.account_name} ({account_type_display})"

    objects = TenantManager()

    def clean(self):
        errors = {}

        if not self.account_type:
            errors['account_type'] = 'Account type is required.'
        elif self.account_type not in dict(self.ACCOUNT_TYPE_CHOICES):
            errors['account_type'] = 'Invalid account type.'

        if not self.account_name or not self.account_name.strip():
            errors['account_name'] = 'Account name is required.'
        elif len(self.account_name.strip()) > 255:
            errors['account_name'] = 'Account name cannot exceed 255 characters.'

        if self.bank_name and len(self.bank_name.strip()) > 255:
            errors['bank_name'] = 'Bank name cannot exceed 255 characters.'

        if self.account_number and len(self.account_number.strip()) > 100:
            errors['account_number'] = 'Account number cannot exceed 100 characters.'

        if self.account_holders_name and len(self.account_holders_name.strip()) > 255:
            errors['account_holders_name'] = 'Account holder name cannot exceed 255 characters.'

        if self.balance is not None and self.balance < Decimal('0.00'):
            errors['balance'] = 'Balance cannot be negative.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

