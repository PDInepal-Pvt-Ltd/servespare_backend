from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel
from apps.base.managers import TenantManager
from django.conf import settings
import re


def validate_phone_number(value):
    """Validate Nepali phone number format."""
    if not value:
        return

    cleaned = re.sub(r'[\s\-\(\)]', '', value)

    if cleaned.startswith('+977'):
        cleaned = cleaned[4:]
    elif cleaned.startswith('977'):
        cleaned = cleaned[3:]

    if not cleaned.isdigit():
        raise ValidationError(
            _('Phone number must contain only digits, spaces, hyphens, parentheses, or +977 for international format.'),
            code='invalid_phone_format'
        )

    if len(cleaned) == 10:
        if not (cleaned.startswith('97') or cleaned.startswith('98')):
            raise ValidationError(
                _('Nepali mobile number must start with 97 or 98.'),
                code='invalid_mobile_prefix'
            )
    elif 6 <= len(cleaned) <= 8:
        pass
    else:
        raise ValidationError(
            _('Phone number must be either 10 digits (mobile) or 6-8 digits (landline).'),
            code='invalid_phone_length'
        )


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

    # Creator (who added this party)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_parties',
        help_text='User who created this party'
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
        on_delete=models.CASCADE,
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
        help_text='Phone number',
        validators=[validate_phone_number]
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
            models.Index(fields=['created_by']),
        ]

    objects = TenantManager()
    
    def clean(self):
        """Validate all fields"""
        errors = {}
        
        # Validate party_name
        if not self.party_name or not self.party_name.strip():
            errors['party_name'] = 'Party name is required.'
        elif len(self.party_name) < 2:
            errors['party_name'] = 'Party name must be at least 2 characters.'
        
        # Validate party_type and customer_type relationship
        if self.party_type == 'customer' and not self.customer_type:
            errors['customer_type'] = 'Customer type is required when party type is Customer.'
        if self.party_type == 'supplier' and self.customer_type:
            errors['customer_type'] = 'Customer type should not be set for suppliers.'
        
        # Validate contact_person
        if self.contact_person and len(self.contact_person) < 2:
            errors['contact_person'] = 'Contact person name must be at least 2 characters.'
        
        # Validate phone
        if self.phone:
            try:
                validate_phone_number(self.phone)
            except ValidationError as exc:
                errors['phone'] = exc.messages[0] if exc.messages else 'Invalid phone number.'
        
        # Validate email (basic format check)
        if self.email:
            if '@' not in self.email or '.' not in self.email.split('@')[-1]:
                errors['email'] = 'Email address is not valid.'
        
        # Validate address
        if self.address and len(self.address) < 5:
            errors['address'] = 'Address must be at least 5 characters.'
        
        # Validate city and state
        if self.city and len(self.city) < 2:
            errors['city'] = 'City name must be at least 2 characters.'
        if self.state_province and len(self.state_province) < 2:
            errors['state_province'] = 'State/Province must be at least 2 characters.'
        
        # Validate PAN number format (Indian PAN: 10 characters)
        if self.pan_number:
            pan_clean = self.pan_number.strip()
            if len(pan_clean) != 10:
                errors['pan_number'] = 'PAN number must be exactly 10 characters.'
            elif not pan_clean.isalnum():
                errors['pan_number'] = 'PAN number can only contain letters and numbers.'
        
        # Validate credit_limit
        if self.credit_limit < 0:
            errors['credit_limit'] = 'Credit limit cannot be negative.'
        
        # Validate opening_balance
        if self.opening_balance is None:
            self.opening_balance = 0.00
        
        if errors:
            raise ValidationError(errors)
    
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

