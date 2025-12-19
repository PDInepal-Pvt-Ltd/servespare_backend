from django.db import models
from django.core.exceptions import ValidationError
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class Party(BaseModel):
    """
    Model to store party information (suppliers and customers)
    """
    PARTY_TYPE_CHOICES = [
        ('supplier', 'Supplier'),
        ('customer', 'Customer'),
    ]
    
    CUSTOMER_TYPE_CHOICES = [
        ('retail_customer', 'Retail Customer'),
        ('retailer', 'Retailer'),
        ('workshop', 'Workshop'),
        ('distributor', 'Distributor'),
        ('wholesaler', 'Wholesaler'),
    ]
    
    PAYMENT_TERMS_CHOICES = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('7_day_credit', '7 Day Credit'),
        ('15_day_credit', '15 Day Credit'),
        ('30_day_credit', '30 Day Credit'),
        ('45_day_credit', '45 Day Credit'),
    ]
    
    # Party Type
    party_type = models.CharField(
        max_length=20,
        choices=PARTY_TYPE_CHOICES,
        help_text='Type of party: Supplier or Customer'
    )
    
    # Customer Type (only applicable if party_type is 'customer')
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Type of customer (only applicable for customers)'
    )
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parties',
        help_text='Tenant that owns this party'
    )

    # Basic Information
    party_name = models.CharField(
        max_length=255,
        help_text='Name of the party/business'
    )
    contact_person = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Name of the contact person'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parties',
        help_text='Branch that manages this party'
    )
    
    # Contact Information
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Phone number'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text='Email address'
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text='Street address'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='City'
    )
    state_province = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='State or Province'
    )
    
    # Financial Information
    pan_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='PAN (Permanent Account Number)'
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PAYMENT_TERMS_CHOICES,
        default='cash',
        help_text='Payment terms for transactions'
    )
    credit_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Credit limit for the party'
    )
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Opening balance for the party'
    )
    
    class Meta:
        db_table = 'party'
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        ordering = ['party_name']
        indexes = [
            models.Index(fields=['party_type']),
            models.Index(fields=['customer_type']),
            models.Index(fields=['party_name']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]

    objects = TenantManager()
    
    def clean(self):
        """Validate that customer_type is set when party_type is customer"""
        if self.party_type == 'customer' and not self.customer_type:
            raise ValidationError({
                'customer_type': 'Customer type is required when party type is Customer.'
            })
        if self.party_type == 'supplier' and self.customer_type:
            raise ValidationError({
                'customer_type': 'Customer type should not be set for suppliers.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        party_type_display = self.get_party_type_display()
        if self.party_type == 'customer' and self.customer_type:
            customer_type_display = self.get_customer_type_display()
            return f"{self.party_name} ({party_type_display} - {customer_type_display})"
        return f"{self.party_name} ({party_type_display})"

