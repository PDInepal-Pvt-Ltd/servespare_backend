from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class BankAccount(BaseModel):
    """
    Model to store bank account information with support for multiple account types:
    - BANK: Traditional bank accounts
    - ESEWA: eSewa digital wallet
    - FONEPAY: FonePay digital wallet
    - CASH: Physical cash/petty cash
    
    All types stored in a single table with type-specific nullable fields.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('bank', 'Bank Account'),
        ('esewa', 'eSewa'),
        ('fonepay', 'FonePay'),
        ('cash', 'Cash'),
    ]
    
    # Account Type (required)
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        help_text='Type of account: bank, esewa, fonepay, or cash'
    )
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bank_accounts',
        help_text='Tenant that owns this account'
    )

    # General Account Information (required for all types)
    account_name = models.CharField(
        max_length=255,
        help_text='Display name for the account (e.g., "Primary Bank", "Cash Register")'
    )
    
    # Bank-specific fields (required only when account_type = BANK)
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
        help_text='Bank account number (required for bank accounts)'
    )
    
    account_holder_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Name of the account holder (optional for bank accounts)'
    )
    
    # Digital Wallet fields (required when account_type = ESEWA or FONEPAY)
    wallet_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Wallet ID or phone number (required for eSewa/FonePay)'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bank_accounts',
        help_text='Branch associated with this account'
    )
    
    # Running balance for the account (tenant+branch scoped)
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text='Current balance for this account'
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
        """
        Validate account based on account_type:
        - BANK: Requires bank_name, account_number
        - ESEWA/FONEPAY: Requires wallet_id
        - CASH: Only account_name required
        """
        errors = {}

        # Validate account_type
        if not self.account_type:
            errors['account_type'] = 'Account type is required.'
        elif self.account_type not in dict(self.ACCOUNT_TYPE_CHOICES):
            errors['account_type'] = 'Invalid account type.'

        # Validate account_name (required for all types)
        if not self.account_name or not self.account_name.strip():
            errors['account_name'] = 'Account name is required.'
        elif len(self.account_name.strip()) > 255:
            errors['account_name'] = 'Account name cannot exceed 255 characters.'

        # Type-specific validation
        account_type = self.account_type

        # BANK account validation
        if account_type == 'bank':
            if not self.bank_name or not self.bank_name.strip():
                errors['bank_name'] = 'Bank name is required for bank accounts.'
            elif len(self.bank_name.strip()) > 255:
                errors['bank_name'] = 'Bank name cannot exceed 255 characters.'
            
            if not self.account_number or not self.account_number.strip():
                errors['account_number'] = 'Account number is required for bank accounts.'
            elif len(self.account_number.strip()) > 100:
                errors['account_number'] = 'Account number cannot exceed 100 characters.'

        # ESEWA/FONEPAY wallet validation
        elif account_type in ['esewa', 'fonepay']:
            if not self.wallet_id or not self.wallet_id.strip():
                account_type_display = self.get_account_type_display()
                errors['wallet_id'] = f'Wallet ID is required for {account_type_display} accounts.'
            elif len(self.wallet_id.strip()) > 100:
                errors['wallet_id'] = 'Wallet ID cannot exceed 100 characters.'

        # CASH account validation (minimal)
        elif account_type == 'cash':
            pass  # Only account_name is required

        # Optional field validation
        if self.account_holder_name and len(self.account_holder_name.strip()) > 255:
            errors['account_holder_name'] = 'Account holder name cannot exceed 255 characters.'

        if self.balance is not None and self.balance < Decimal('0.00'):
            errors['balance'] = 'Balance cannot be negative.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_account_display_info(self):
        """Get formatted display information based on account type"""
        account_type = self.account_type
        
        if account_type == 'bank':
            return {
                'type': 'Bank Account',
                'identifier': self.account_number,
                'bank': self.bank_name,
                'holder': self.account_holder_name or 'N/A'
            }
        elif account_type == 'esewa':
            return {
                'type': 'eSewa',
                'identifier': self.wallet_id,
                'bank': None,
                'holder': None
            }
        elif account_type == 'fonepay':
            return {
                'type': 'FonePay',
                'identifier': self.wallet_id,
                'bank': None,
                'holder': None
            }
        elif account_type == 'cash':
            return {
                'type': 'Cash',
                'identifier': None,
                'bank': None,
                'holder': None
            }
        
        return None

