import re
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel
from apps.base.managers import TenantManager
from apps.stock_management.models import Inventory


def validate_phone_number(value):
    """
    Validate Nepali phone number format.
    Accepts:
    - Mobile: 10 digits starting with 97 or 98 (e.g., 9841234567)
    - Landline: 6-8 digits with area code (e.g., 01-4445678)
    - International format: +977 followed by mobile/landline
    - Formats accepted: with/without spaces, hyphens, parentheses
    """
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

    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills_created',
        help_text='User who created this bill'
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

    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('13.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Tax percentage (GST/VAT)'
    )

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Tax amount'
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
    
    # Relationships to Invoice and SalesOrder (for online orders)
    invoice = models.OneToOneField(
        'sales.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bill',
        help_text='Related invoice (auto-created from paid invoice for online orders)'
    )
    
    sales_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bills',
        help_text='Related sales order (for online orders)'
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
            models.Index(fields=['invoice']),
            models.Index(fields=['sales_order']),
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
        errors = {}

        # Customer info validation
        if not self.customer_name or not self.customer_name.strip():
            errors['customer_name'] = 'Customer name is required.'
        elif len(self.customer_name.strip()) < 2:
            errors['customer_name'] = 'Customer name must be at least 2 characters.'
        elif len(self.customer_name.strip()) > 255:
            errors['customer_name'] = 'Customer name cannot exceed 255 characters.'

        if not self.customer_type:
            errors['customer_type'] = 'Customer type is required.'

        if self.address:
            addr = self.address.strip()
            if len(addr) < 5:
                errors['address'] = 'Address must be at least 5 characters when provided.'
            elif len(addr) > 2000:
                errors['address'] = 'Address cannot exceed 2000 characters.'

        if self.phone_numbers:
            phones = [p.strip() for p in self.phone_numbers.split(',') if p.strip()]
            if not phones:
                errors['phone_numbers'] = 'Provide at least one phone number or leave blank.'
            for phone in phones:
                try:
                    validate_phone_number(phone)
                except ValidationError as exc:
                    errors['phone_numbers'] = '; '.join(exc.messages)
                    break
                if len(phone) > 20:
                    errors['phone_numbers'] = 'Each phone number cannot exceed 20 characters.'
                    break

        if self.pan_vat_number:
            pan_val = self.pan_vat_number.strip()
            if not pan_val.isdigit():
                errors['pan_vat_number'] = 'PAN/VAT number must be numeric.'
            elif len(pan_val) != 9:
                errors['pan_vat_number'] = 'PAN/VAT number must be exactly 9 digits.'

        # Billing fields
        if self.price is not None:
            if self.price < 0:
                errors['price'] = 'Price cannot be negative.'
            elif self.price > 999999.99:
                errors['price'] = 'Price cannot exceed 999,999.99.'

        if self.discount_value is None:
            self.discount_value = 0

        if self.discount_value < 0:
            errors['discount_value'] = 'Discount value cannot be negative.'
        elif self.discount_value > 999999.99:
            errors['discount_value'] = 'Discount value cannot exceed 999,999.99.'

        if not self.discount_method:
            self.discount_method = 'amount'

        if self.discount_method not in dict(self.DISCOUNT_METHOD_CHOICES):
            errors['discount_method'] = 'Invalid discount method.'

        if self.discount_method == 'percentage':
            if self.discount_value is not None and self.discount_value > 100:
                errors['discount_value'] = 'Percentage discount cannot exceed 100%.'
        else:  # amount or None
            # Compare against price if provided, otherwise allow non-negative checked above
            if (
                self.discount_value is not None and self.price is not None and
                self.discount_value > self.price
            ):
                errors['discount_value'] = 'Discount amount cannot exceed the price.'

        if self.tax_percentage is None:
            self.tax_percentage = Decimal('13.00')
        elif self.tax_percentage < 0:
            errors['tax_percentage'] = 'Tax percentage cannot be negative.'
        elif self.tax_percentage > Decimal('100.00'):
            errors['tax_percentage'] = 'Tax percentage cannot exceed 100%.'

        if self.tax_amount is not None and self.tax_amount < 0:
            errors['tax_amount'] = 'Tax amount cannot be negative.'

        # Payment fields
        if not self.payment_method:
            errors['payment_method'] = 'Payment method is required.'
        elif self.payment_method not in dict(self.PAYMENT_METHOD_CHOICES):
            errors['payment_method'] = 'Invalid payment method.'

        if not self.status:
            errors['status'] = 'Status is required.'
        elif self.status not in dict(self.STATUS_CHOICES):
            errors['status'] = 'Invalid status.'

        if errors:
            raise ValidationError(errors)

    objects = TenantManager()

    # Removed the previous inventory product relationship
    # Updated methods to handle purchase items instead
    def calculate_total(self):
        total_before_tax = self.total_after_discount
        tax_value = self.calculate_tax_amount()
        return total_before_tax + tax_value

    def calculate_tax_amount(self):
        base_amount = self.total_after_discount
        percentage = self.tax_percentage if self.tax_percentage is not None else Decimal('13.00')
        tax_value = (base_amount * percentage) / Decimal('100.00')
        return tax_value.quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        # Ensure a default 13% tax is applied when not explicitly set
        if self.tax_percentage is None:
            self.tax_percentage = Decimal('13.00')
        
        # Skip tax calculation if explicitly disabled (e.g., when creating from invoice)
        if not getattr(self, '_skip_tax_calculation', False):
            self.tax_amount = self.calculate_tax_amount()
        
        super().save(*args, **kwargs)

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
        """
        Decrease inventory quantities for all purchase items in this bill
        Note: This is now primarily handled via signals on bill creation and purchase item addition.
        This method can still be called explicitly if needed.
        """
        from decimal import Decimal
        for item in self.purchase_items.all():
            if item.inventory and item.quantity > 0:
                current_qty = item.inventory.quantity
                new_qty = max(Decimal('0.00'), current_qty - item.quantity)
                # Only update if quantity actually needs to decrease
                if new_qty < current_qty:
                    item.inventory.quantity = new_qty
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
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from decimal import Decimal

        errors = {}

        if not self.bill_id and not self.bill:
            errors['bill'] = 'Bill is required.'

        if not self.inventory_id and not self.inventory:
            errors['inventory'] = 'Inventory item is required.'

        if self.quantity is None:
            errors['quantity'] = 'Quantity is required.'
        elif self.quantity <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'
        elif self.quantity > Decimal('999999.99'):
            errors['quantity'] = 'Quantity cannot exceed 999,999.99.'

        price_value = self.price if self.price is not None else Decimal('0.00')
        if price_value < 0:
            errors['price'] = 'Price cannot be negative.'
        elif price_value > Decimal('999999.99'):
            errors['price'] = 'Price cannot exceed 999,999.99.'

        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Auto-populate price from inventory if not provided"""
        if (self.price is None or self.price == 0) and self.inventory:
            # Use retail_pricing if available, otherwise use base price
            self.price = self.inventory.retail_pricing or self.inventory.price or 0
        self.full_clean()
        super().save(*args, **kwargs)

    def total_price(self):
        """Calculate total price for this purchase item (quantity * price)"""
        from decimal import Decimal
        quantity = self.quantity or Decimal('0.00')
        price = self.price or Decimal('0.00')
        return quantity * price
