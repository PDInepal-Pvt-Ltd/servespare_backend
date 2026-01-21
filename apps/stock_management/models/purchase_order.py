from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, FileExtensionValidator
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class PurchaseOrder(BaseModel):
    """
    Model to store purchase orders
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('billed', 'Billed'),
        ('returned', 'Returned'),

    ]
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text='Tenant that owns this purchase order'
    )

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

    invoice_pdf = models.FileField(
        upload_to='purchase_invoices/pdfs/',
        validators=[FileExtensionValidator(['pdf'])],
        blank=True,
        null=True,
        help_text='Upload supplier invoice in PDF format'
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
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]

    objects = TenantManager()
    
    def clean(self):
        """Validate all fields"""
        errors = {}
        
        # Validate po_number
        if not self.po_number or not self.po_number.strip():
            errors['po_number'] = 'PO number is required.'
        elif len(self.po_number) < 2:
            errors['po_number'] = 'PO number must be at least 2 characters.'
        
        # Validate supplier
        if not self.supplier:
            errors['supplier'] = 'Supplier is required.'
        elif self.supplier.party_type != 'supplier':
            errors['supplier'] = 'Selected party must be a supplier.'
        
        # Validate order_date
        if not self.order_date:
            errors['order_date'] = 'Order date is required.'
        
        # Validate expected_delivery_date
        if self.expected_delivery_date and self.order_date:
            if self.expected_delivery_date < self.order_date:
                errors['expected_delivery_date'] = 'Expected delivery date cannot be before order date.'
        
        # Validate status
        if not self.status:
            errors['status'] = 'Status is required.'
        
        # Validate notes
        if self.notes and len(self.notes) > 5000:
            errors['notes'] = 'Notes cannot exceed 5000 characters.'
        
        # Validate terms_and_condition
        if self.terms_and_condition and len(self.terms_and_condition) > 5000:
            errors['terms_and_condition'] = 'Terms and conditions cannot exceed 5000 characters.'
        
        if errors:
            raise ValidationError(errors)
    
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
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='purchase_order_items',
        help_text='Tenant that owns this purchase order item'
    )

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
        default=Decimal('13.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Tax percentage (e.g., 18.00 for 18%)'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Discount amount in currency'
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

    objects = TenantManager()
    
    def clean(self):
        """Validate all fields"""
        errors = {}
        
        # Validate item_name
        if not self.item_name or not self.item_name.strip():
            errors['item_name'] = 'Item name is required.'
        elif len(self.item_name) < 2:
            errors['item_name'] = 'Item name must be at least 2 characters.'
        
        # Validate part_number
        if self.part_number and len(self.part_number) < 2:
            errors['part_number'] = 'Part number must be at least 2 characters.'
        
        # Validate quantity
        if not self.quantity or self.quantity <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'
        if self.quantity and self.quantity > 999999.99:
            errors['quantity'] = 'Quantity cannot exceed 999,999.99.'
        
        # Validate unit_price
        if self.unit_price < 0:
            errors['unit_price'] = 'Unit price cannot be negative.'
        if self.unit_price > 999999.99:
            errors['unit_price'] = 'Unit price cannot exceed 999,999.99.'
        
        # Validate tax
        if self.tax < 0:
            errors['tax'] = 'Tax percentage cannot be negative.'
        if self.tax > 100:
            errors['tax'] = 'Tax percentage cannot exceed 100%.'
        
        # Validate discount_amount
        if self.discount_amount < 0:
            errors['discount_amount'] = 'Discount amount cannot be negative.'
        if self.discount_amount > self.subtotal:
            errors['discount_amount'] = 'Discount amount cannot exceed subtotal.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        """Calculate subtotal before tax and discount"""
        return self.quantity * self.unit_price
    
    @property
    def subtotal_after_discount(self):
        """Calculate subtotal after discount"""
        return self.subtotal - self.discount_amount
    
    @property
    def tax_amount(self):
        """Calculate tax amount on discounted subtotal"""
        subtotal_after_discount = self.subtotal_after_discount
        return (subtotal_after_discount * self.tax) / Decimal('100.00')
    
    @property
    def total_price(self):
        """Calculate total price including tax and discount"""
        return self.subtotal_after_discount + self.tax_amount
    
    def __str__(self):
        return f"{self.item_name} - Qty: {self.quantity} (PO: {self.purchase_order.po_number})"

