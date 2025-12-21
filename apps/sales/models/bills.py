from django.db import models
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class Bill(BaseModel):
    """
    Model to store bills/invoices
    """
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("pending", "Pending"),
        ("on_hold", "On Hold"),
        ("credit_sale", "Credit Sale"),
        ("draft", "Draft"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("bank_transfer", "Bank Transfer"),
    ]

    DISCOUNT_METHOD_CHOICES = [
        ("amount", "Amount"),
        ("percentage", "Percentage"),
    ]
    CUSTOMER_TYPE_CHOICES = [
        ('retail', 'Retail'),
        ('retailer', 'Retailer'),
        ('wholesaler', 'Wholesaler'),
        ('distributor', 'Distributor'),
        ('workshop', 'Workshop'),
    ]
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bills',
        help_text='Tenant that owns this bill'
    )

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

    # Billing fields
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Base price before discount"
    )

    discount_method = models.CharField(
        max_length=12,
        choices=DISCOUNT_METHOD_CHOICES,
        default="amount",
        blank=True,
        null=True,
        help_text="Discount method: Amount or Percentage"
    )

    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        null=True,
        help_text="If Percentage, enter percent (0-100). If Amount, enter currency value."
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="cash",
        blank=True,
        null=True,
        help_text="Payment method used for the bill"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        blank=True,
        null=True,
        help_text="Bill status: Draft, Pending, Paid, On Hold, Credit Sale, Cancelled, or Refunded"
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills',
        help_text='Branch issuing this bill'
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
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]
    
    def __str__(self):
        customer_type_display = self.get_customer_type_display()
        return f"{self.customer_name} ({customer_type_display})"

    @property
    def discount_amount(self):
        if self.discount_method == 'percentage':
            return (self.price or 0) * (self.discount_value or 0) / 100
        return self.discount_value or 0

    @property
    def total_after_discount(self):
        base = self.price or 0
        disc = self.discount_amount or 0
        total = base - disc
        return total if total >= 0 else 0

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.price is not None and self.price < 0:
            raise ValidationError({
                'price': 'Price cannot be negative.'
            })

        if self.discount_value is None:
            self.discount_value = 0

        if self.discount_value < 0:
            raise ValidationError({
                'discount_value': 'Discount value cannot be negative.'
            })

        if self.discount_method == 'percentage':
            if self.discount_value is not None and self.discount_value > 100:
                raise ValidationError({
                    'discount_value': 'Percentage discount cannot exceed 100%.'
                })
        else:  # amount or None
            if (
                self.discount_value is not None and self.price is not None and
                self.discount_value > self.price
            ):
                raise ValidationError({
                    'discount_value': 'Discount amount cannot exceed the price.'
                })

    objects = TenantManager()

