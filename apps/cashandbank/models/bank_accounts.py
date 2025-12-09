from django.db import models
from apps.base.models import BaseModel


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
    
    class Meta:
        db_table = 'bank_account'
        verbose_name = 'Bank Account'
        verbose_name_plural = 'Bank Accounts'
        ordering = ['account_name']
        indexes = [
            models.Index(fields=['account_type']),
            models.Index(fields=['account_name']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        account_type_display = self.get_account_type_display()
        return f"{self.account_name} ({account_type_display})"

