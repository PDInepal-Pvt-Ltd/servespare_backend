from django.db import models
from apps.base.models import BaseModel
from apps.base.managers import TenantManager
from apps.stock_management.models import Inventory


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
    def subtotal(self):
        """Calculate subtotal from all purchase items"""
        from decimal import Decimal
        total = Decimal('0.00')
        for item in self.purchase_items.all():
            total += item.total_price()
        return total

    @property
    def discount_amount(self):
        """Calculate discount amount based on subtotal and discount method"""
        subtotal = self.subtotal
        if self.discount_method == 'percentage':
            return subtotal * (self.discount_value or 0) / 100
        return self.discount_value or 0

    @property
    def total_after_discount(self):
        """Calculate total after applying discount"""
        subtotal = self.subtotal
        disc = self.discount_amount
        total = subtotal - disc
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

    # Removed the previous inventory product relationship
    # Updated methods to handle purchase items instead
    def calculate_total(self):
        total = self.price or 0
        for item in self.purchase_items.all():
            total += item.total_price()  # Calculate total based on purchase items
        return total

    def update_bill(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

    @classmethod
    def get_bill(cls, bill_id):
        return cls.objects.get(id=bill_id)

    @classmethod
    def delete_bill(cls, bill_id):
        cls.objects.filter(id=bill_id).delete()

    def decrease_inventory(self):
        """Decrease inventory quantities for all purchase items in this bill"""
        from decimal import Decimal
        for item in self.purchase_items.all():
            if item.inventory and item.quantity > 0:
                item.inventory.quantity = max(
                    Decimal('0.00'),
                    item.inventory.quantity - item.quantity
                )
                item.inventory.save(update_fields=['quantity', 'modified'])


class PurchaseItem(models.Model):
    """
    Model to store details of products purchased in a bill
    """
    bill = models.ForeignKey(
        'Bill',
        on_delete=models.CASCADE,
        related_name='purchase_items',
        help_text='Bill associated with this purchase item'
    )
    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='purchase_items',
        help_text='Inventory item being purchased'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Quantity of the product'
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Price of the product at the time of purchase (auto-populated from inventory)'
    )
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'purchase_item'
        verbose_name = 'Purchase Item'
        verbose_name_plural = 'Purchase Items'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['bill']),
            models.Index(fields=['inventory']),
        ]

    def __str__(self):
        return f"{self.inventory.item_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        """Auto-populate price from inventory if not provided"""
        if not self.price and self.inventory:
            # Use retail_pricing if available, otherwise use base price
            self.price = self.inventory.retail_pricing or self.inventory.price or 0
        super().save(*args, **kwargs)
