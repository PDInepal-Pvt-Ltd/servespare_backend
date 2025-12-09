from django.db import models
from apps.base.models import BaseModel


class Bill(BaseModel):
    """
    Model to store bills/invoices
    """
    CUSTOMER_TYPE_CHOICES = [
        ('retail', 'Retail'),
        ('retailer', 'Retailer'),
        ('wholesaler', 'Wholesaler'),
        ('distributor', 'Distributor'),
        ('workshop', 'Workshop'),
    ]
    
    # Customer Information
    customer_name = models.CharField(
        max_length=255,
        help_text='Name of the customer'
    )
    
    address = models.TextField(
        blank=True,
        null=True,
        help_text='Customer address'
    )
    
    phone_numbers = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Phone numbers (can include multiple numbers separated by comma)'
    )
    
    pan_vat_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='PAN/VAT number of the customer'
    )
    
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        help_text='Type of customer: Retail, Retailer, Wholesaler, Distributor, or Workshop'
    )
    
    class Meta:
        db_table = 'bill'
        verbose_name = 'Bill'
        verbose_name_plural = 'Bills'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['customer_type']),
            models.Index(fields=['customer_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created']),
        ]
    
    def __str__(self):
        customer_type_display = self.get_customer_type_display()
        return f"{self.customer_name} ({customer_type_display})"

