from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.base.models import BaseModel


class PurchaseOrder(BaseModel):
    """
    Model to store purchase orders
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('billed', 'Billed'),
    ]
    
    # Basic Information
    po_number = models.CharField(
        max_length=100,
        unique=True,
        help_text='Purchase Order Number'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Status of the purchase order'
    )
    supplier = models.ForeignKey(
        'stock_management.Party',
        on_delete=models.CASCADE,
        limit_choices_to={'party_type': 'supplier'},
        related_name='purchase_orders',
        help_text='Supplier for this purchase order'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text='Branch placing this purchase order'
    )
    order_date = models.DateField(
        help_text='Date when the order was placed'
    )
    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
        help_text='Expected delivery date'
    )
    
    # File Upload
    purchase_invoice = models.FileField(
        upload_to='purchase_invoices/',
        blank=True,
        null=True,
        help_text='Upload purchase invoice document'
    )
    
    # Additional Information
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes'
    )
    terms_and_condition = models.TextField(
        blank=True,
        null=True,
        help_text='Terms and conditions'
    )
    
    class Meta:
        db_table = 'purchase_order'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-order_date', '-created']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['supplier']),
        ]
    
    def clean(self):
        """Validate dates"""
        if self.expected_delivery_date and self.order_date:
            if self.expected_delivery_date < self.order_date:
                raise ValidationError({
                    'expected_delivery_date': 'Expected delivery date cannot be before order date.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.party_name} ({self.get_status_display()})"
    
    @property
    def total_amount(self):
        """Calculate total amount including all items"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def total_tax(self):
        """Calculate total tax"""
        return sum(item.tax_amount for item in self.items.all())


class PurchaseOrderItem(BaseModel):
    """
    Model to store items in a purchase order
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Purchase order this item belongs to'
    )
    item_name = models.CharField(
        max_length=255,
        help_text='Name of the item'
    )
    part_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Part number or SKU'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Quantity ordered'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price per unit'
    )
    tax = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Tax percentage (e.g., 18.00 for 18%)'
    )
    discount_description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Description of discount applied'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_order_items',
        help_text='Branch responsible for this purchase item'
    )
    
    class Meta:
        db_table = 'purchase_order_item'
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
        ordering = ['purchase_order', 'id']
    
    def clean(self):
        """Validate item data"""
        if self.quantity <= 0:
            raise ValidationError({
                'quantity': 'Quantity must be greater than zero.'
            })
        if self.unit_price < 0:
            raise ValidationError({
                'unit_price': 'Unit price cannot be negative.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        """Calculate subtotal before tax"""
        return self.quantity * self.unit_price
    
    @property
    def tax_amount(self):
        """Calculate tax amount"""
        subtotal = self.subtotal
        return (subtotal * self.tax) / Decimal('100.00')
    
    @property
    def total_price(self):
        """Calculate total price including tax"""
        return self.subtotal + self.tax_amount
    
    def __str__(self):
        return f"{self.item_name} - Qty: {self.quantity} (PO: {self.purchase_order.po_number})"

