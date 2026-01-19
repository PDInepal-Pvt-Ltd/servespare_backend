from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager
import uuid


class Invoice(BaseModel):
    """
    Model to store sales invoices generated from orders
    """
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Tenant that owns this invoice'
    )

    # Invoice Information
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text='Unique invoice number'
    )
    invoice_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date and time when invoice was created'
    )

    # Reference to Sales Order and Bill
    sales_order = models.OneToOneField(
        'sales.SalesOrder',
        on_delete=models.PROTECT,
        related_name='invoice',
        null=True,
        blank=True,
        help_text='Associated sales order'
    )
    bill = models.OneToOneField(
        'sales.Bill',
        on_delete=models.SET_NULL,
        related_name='invoice',
        null=True,
        blank=True,
        help_text='Associated bill/invoice'
    )

    # Customer Information
    customer = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text='Customer who placed the order'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Branch issuing this invoice'
    )

    # Financial Information
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Subtotal before tax and discount'
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Discount percentage'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Discount amount'
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
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
    shipping_charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Shipping/delivery charges'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Final total amount'
    )

    due_date = models.DateField(
        blank=True,
        null=True,
        help_text='Invoice due date'
    )
    
    # Payment Information
    # Payment Status & Method (snapshot fields, updated by Payment model)
    payment_status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('paid', 'Paid'),
            ('pending', 'Pending'),
            ('partial', 'Partial'),
            ('on_hold', 'On Hold'),
            ('credit_sale', 'Credit Sale'),
            ('cancelled', 'Cancelled'),
            ('refunded', 'Refunded'),
        ],
        help_text='Payment status (computed from payments)'
    )
    payment_method = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('upi', 'UPI'),
            ('bank_transfer', 'Bank Transfer'),
            ('credit', 'Credit'),
        ],
        help_text='Latest payment method used'
    )
    
    payment_date = models.DateField(
        blank=True,
        null=True,
        help_text='Date when payment was received'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Invoice notes or special instructions'
    )

    # Staff Information
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_invoices',
        help_text='User who created this invoice'
    )

    class Meta:
        db_table = 'invoice'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-invoice_date', '-created']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['customer']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['-invoice_date']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
            models.Index(fields=['sales_order']),
            models.Index(fields=['bill']),
        ]

    objects = TenantManager()

    def save(self, *args, **kwargs):
        """Generate invoice number if not exists"""
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        self.full_clean()
        super().save(*args, **kwargs)

    def generate_invoice_number(self):
        """Generate unique invoice number"""
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4().hex[:6].upper())
        return f"INV-{date_str}-{unique_id}"

    def calculate_totals(self):
        """Calculate invoice totals from items"""
        items = self.items.all()

        # Calculate subtotal from items
        self.subtotal = sum(item.line_total for item in items)

        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (self.subtotal * self.discount_percentage) / Decimal('100.00')

        # Calculate amount after discount
        amount_after_discount = self.subtotal - self.discount_amount

        # Calculate tax
        if self.tax_percentage > 0:
            self.tax_amount = (amount_after_discount * self.tax_percentage) / Decimal('100.00')

        # Calculate total
        self.total_amount = amount_after_discount + self.tax_amount + self.shipping_charges

        self.save(update_fields=[
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount', 'modified'
        ])

    def clean(self):
        errors = {}

        if not self.customer_id and not self.customer:
            errors['customer'] = 'Customer is required.'

        # Financial validations
        money_fields = {
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'tax_amount': self.tax_amount,
            'shipping_charges': self.shipping_charges,
            'total_amount': self.total_amount,
        }
        for field, value in money_fields.items():
            if value is not None and value < 0:
                errors[field] = f"{field.replace('_', ' ').title()} cannot be negative."

        if self.discount_percentage is not None and self.discount_percentage > Decimal('100.00'):
            errors['discount_percentage'] = 'Discount percentage cannot exceed 100%.'

        if self.tax_percentage is not None and self.tax_percentage > Decimal('100.00'):
            errors['tax_percentage'] = 'Tax percentage cannot exceed 100%.'

        # Ensure discount_amount does not exceed subtotal
        if self.subtotal is not None and self.discount_amount is not None:
            if self.discount_amount > self.subtotal:
                errors['discount_amount'] = 'Discount amount cannot exceed subtotal.'

        # Ensure total is logical
        if self.total_amount is not None and self.total_amount < Decimal('0.00'):
            errors['total_amount'] = 'Total amount cannot be negative.'

        if self.payment_method:
            valid_methods = [choice[0] for choice in self._meta.get_field('payment_method').choices]
            if self.payment_method not in valid_methods:
                errors['payment_method'] = 'Invalid payment method.'

        if self.payment_status:
            valid_statuses = [choice[0] for choice in self._meta.get_field('payment_status').choices]
            if self.payment_status not in valid_statuses:
                errors['payment_status'] = 'Invalid payment status.'

        if errors:
            raise ValidationError(errors)

    @property
    def balance_amount(self):
        return self.total_amount - Decimal('0.00')

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def total_items(self):
        return self.items.count()

    def __str__(self):
        customer_name = self.customer.full_name or self.customer.username
        return f"{self.invoice_number} - {customer_name} - {self.payment_status}"


class InvoiceItem(BaseModel):
    """
    Model to store individual items in an invoice
    """
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invoice_items',
        help_text='Tenant that owns this invoice item'
    )

    # Invoice Reference
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Invoice this item belongs to'
    )

    # Product Information
    inventory = models.ForeignKey(
        'stock_management.Inventory',
        on_delete=models.PROTECT,
        related_name='invoice_items',
        help_text='Inventory item on invoice'
    )

    # Item Details
    item_name = models.CharField(
        max_length=255,
        help_text='Item name (snapshot at time of invoice)'
    )
    part_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Part number (snapshot)'
    )

    # Quantity and Pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Quantity on invoice'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price per unit'
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Discount percentage on this item'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Discount amount'
    )
    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Tax percentage'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Tax amount'
    )
    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total amount for this line item'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Notes for this item'
    )

    class Meta:
        db_table = 'invoice_item'
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
        ordering = ['invoice', 'created']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['inventory']),
            models.Index(fields=['tenant']),
        ]

    def save(self, *args, **kwargs):
        """Calculate line totals and snapshot item details"""
        # Snapshot inventory details if new
        if not self.pk and self.inventory:
            self.item_name = self.inventory.item_name
            self.part_number = self.inventory.part_number

            # Auto-set price from inventory if not provided
            if not self.unit_price or self.unit_price == Decimal('0.00'):
                self.unit_price = self.inventory.retail_pricing or self.inventory.price

        # Calculate discount amount
        gross_amount = self.quantity * self.unit_price
        if self.discount_percentage > 0:
            self.discount_amount = (gross_amount * self.discount_percentage) / Decimal('100.00')

        # Calculate amount after discount
        amount_after_discount = gross_amount - self.discount_amount

        # Calculate tax
        if self.tax_percentage > 0:
            self.tax_amount = (amount_after_discount * self.tax_percentage) / Decimal('100.00')

        # Calculate line total
        self.line_total = amount_after_discount + self.tax_amount
        self.full_clean()

        super().save(*args, **kwargs)

        # Recalculate invoice totals
        self.invoice.calculate_totals()

    def clean(self):
        errors = {}

        if not self.invoice_id and not self.invoice:
            errors['invoice'] = 'Invoice is required.'

        if not self.inventory_id and not self.inventory:
            errors['inventory'] = 'Inventory item is required.'

        if not self.item_name or not self.item_name.strip():
            errors['item_name'] = 'Item name is required.'
        elif len(self.item_name.strip()) > 255:
            errors['item_name'] = 'Item name cannot exceed 255 characters.'

        if self.part_number and len(self.part_number.strip()) > 100:
            errors['part_number'] = 'Part number cannot exceed 100 characters.'

        # Numeric validations
        if self.quantity is None or self.quantity <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'

        if self.unit_price is None or self.unit_price < 0:
            errors['unit_price'] = 'Unit price cannot be negative.'

        if self.discount_percentage is not None and self.discount_percentage > Decimal('100.00'):
            errors['discount_percentage'] = 'Discount percentage cannot exceed 100%.'

        gross_amount = self.quantity * self.unit_price if self.quantity and self.unit_price is not None else Decimal('0.00')

        if self.discount_amount is not None and self.discount_amount < 0:
            errors['discount_amount'] = 'Discount amount cannot be negative.'
        elif self.discount_amount is not None and gross_amount and self.discount_amount > gross_amount:
            errors['discount_amount'] = 'Discount amount cannot exceed gross amount.'

        if self.tax_percentage is not None and self.tax_percentage > Decimal('100.00'):
            errors['tax_percentage'] = 'Tax percentage cannot exceed 100%.'

        if self.tax_amount is not None and self.tax_amount < 0:
            errors['tax_amount'] = 'Tax amount cannot be negative.'

        if self.line_total is not None and self.line_total < 0:
            errors['line_total'] = 'Line total cannot be negative.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.item_name} x {self.quantity}"
