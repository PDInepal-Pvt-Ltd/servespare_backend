from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager
import uuid


class SalesOrder(BaseModel):
    """
    Model to store sales orders
    """
    ORDER_STATUS_CHOICES = [
        ('confirmed', 'Confirmed Order'),
        ('ready_to_pack', 'Ready to Pack'),
        ('packed', 'Packed'),
        ('ready_to_depart', 'Ready to Depart'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sales_orders',
        help_text='Tenant that owns this sales order'
    )

    # Order Information
    order_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text='Unique order number'
    )
    order_date = models.DateTimeField(
        auto_now_add=True,
        help_text='Date and time when order was created'
    )
    
    # Customer Information
    customer = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='sales_orders',
        help_text='User/Customer who placed the order'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        help_text='Branch handling this order'
    )
    
    # Order Status
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='confirmed',
        help_text='Current status of the order'
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
    
    # Delivery Information
    delivery_address = models.TextField(
        help_text='Delivery address'
    )
    delivery_city = models.CharField(
        max_length=100,
        help_text='Delivery city'
    )
    delivery_state = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Delivery state'
    )
    delivery_pincode = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Delivery pincode'
    )
    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
        help_text='Expected delivery date'
    )
    actual_delivery_date = models.DateField(
        blank=True,
        null=True,
        help_text='Actual delivery date'
    )
    

    
    # Tracking Information
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Courier tracking number'
    )
    courier_partner = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Courier partner name'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Order notes or special instructions'
    )
    internal_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Internal notes (not visible to customer)'
    )
    
    # Staff Information
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_orders',
        help_text='User who created this order'
    )
    
    class Meta:
        db_table = 'sales_order'
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
        ordering = ['-order_date', '-created']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer']),
            models.Index(fields=['order_status']),
            models.Index(fields=['order_date']),
            models.Index(fields=['-order_date']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]

    objects = TenantManager()
    
    def save(self, *args, **kwargs):
        """Generate order number if not exists and calculate totals"""
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        # Delivery address must be provided explicitly
        # (User model doesn't have address fields)
        
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4().hex[:6].upper())
        return f"SO-{date_str}-{unique_id}"
    
    def calculate_totals(self):
        """Calculate order totals from items"""
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
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount', 
            'modified'
        ])
    
    def update_order_status(self, new_status):
        """Update order status"""
        if new_status not in dict(self.ORDER_STATUS_CHOICES):
            raise ValidationError(f"Invalid status: {new_status}")
        
        self.order_status = new_status
        
        # Auto-update delivery date when delivered
        if new_status == 'delivered' and not self.actual_delivery_date:
            from django.utils import timezone
            self.actual_delivery_date = timezone.now().date()

        # On delivered, deduct inventory for all items not yet deducted
        if new_status == 'delivered':
            for item in self.items.select_related('inventory').all():
                item.deduct_inventory()
        
        self.save(update_fields=['order_status', 'actual_delivery_date', 'modified'])
    
    def cancel_order(self):
        """Cancel order and restore inventory"""
        if self.order_status == 'cancelled':
            raise ValidationError("Order is already cancelled")
        if self.order_status == 'delivered':
            raise ValidationError("Cannot cancel a delivered order")
        
        # Restore inventory for all items that were deducted
        for item in self.items.select_related('inventory').all():
            if item.inventory_deducted:
                item.restore_inventory()
        
        self.order_status = 'cancelled'
        self.save(update_fields=['order_status', 'modified'])
    
    # -------- Properties --------
    @property
    def balance_amount(self):
        return Decimal('0.00')
    
    @property
    def total_items(self):
        """Get total number of items"""
        return self.items.count()
    
    @property
    def total_quantity(self):
        """Get total quantity of all items"""
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def status_display_description(self):
        """Get detailed status description"""
        status_descriptions = {
            'confirmed': 'Order confirmed by customer and ready to process',
            'ready_to_pack': 'Items ready to be picked and packed',
            'packed': 'Items packed and ready for dispatch',
            'ready_to_depart': 'Package ready for courier pickup',
            'in_transit': 'Package dispatched and on the way to customer',
            'delivered': 'Order delivered to customer successfully',
            'cancelled': 'Order has been cancelled',
        }
        return status_descriptions.get(self.order_status, '')
    
    def generate_invoice(self):
        """Generate invoice from this sales order"""
        from apps.sales.models import Invoice, InvoiceItem
        
        # Check if invoice already exists
        if hasattr(self, 'invoice'):
            return self.invoice
        
        # Create invoice
        invoice = Invoice.objects.create(
            tenant=self.tenant,
            customer=self.customer,
            branch=self.branch,
            sales_order=self,
            subtotal=self.subtotal,
            discount_percentage=self.discount_percentage,
            discount_amount=self.discount_amount,
            tax_percentage=self.tax_percentage,
            tax_amount=self.tax_amount,
            shipping_charges=self.shipping_charges,
            total_amount=self.total_amount,
            created_by=self.created_by,
        )
        
        # Create invoice items from order items
        for order_item in self.items.all():
            InvoiceItem.objects.create(
                tenant=self.tenant,
                invoice=invoice,
                inventory=order_item.inventory,
                item_name=order_item.item_name,
                part_number=order_item.part_number,
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
                discount_percentage=order_item.discount_percentage,
                discount_amount=order_item.discount_amount,
                tax_percentage=order_item.tax_percentage,
                tax_amount=order_item.tax_amount,
                line_total=order_item.line_total,
                notes=order_item.notes,
            )
        
        return invoice
    
    
    def _map_payment_status_to_invoice(self):
        """Map sales order payment status to invoice payment status"""
        status_map = {
            'paid': 'paid',
            'partial': 'pending',
            'pending': 'pending',
            'on_hold': 'on_hold',
            'credit_sale': 'credit_sale',
            'cancelled': 'cancelled',
            'refunded': 'refunded',
        }
        return status_map.get(self.payment_status, 'pending')

    def __str__(self):
        customer_name = self.customer.full_name or self.customer.username
        return f"{self.order_number} - {customer_name} - {self.get_order_status_display()}"



class SalesOrderItem(BaseModel):
    """
    Model to store individual items in a sales order
    """
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sales_order_items',
        help_text='Tenant that owns this sales order item'
    )

    # Order Reference
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Sales order this item belongs to'
    )
    
    # Product Information
    inventory = models.ForeignKey(
        'stock_management.Inventory',
        on_delete=models.PROTECT,
        related_name='sales_items',
        help_text='Inventory item being sold'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_order_items',
        help_text='Branch fulfilling this item'
    )
    
    # Item Details
    item_name = models.CharField(
        max_length=255,
        help_text='Item name (snapshot at time of order)'
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
        help_text='Quantity ordered'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price per unit (auto-filled from inventory retail_pricing)'
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
    
    # Warranty
    warranty_period = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Warranty period (snapshot from inventory)'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Notes for this item'
    )
    
    class Meta:
        db_table = 'sales_order_item'
        verbose_name = 'Sales Order Item'
        verbose_name_plural = 'Sales Order Items'
        ordering = ['order', 'created']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['inventory']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]
    # Inventory deduction flag
    inventory_deducted = models.BooleanField(
        default=False,
        help_text='Whether inventory has been deducted for this item upon delivery'
    )
    
    def save(self, *args, **kwargs):
        """Calculate line totals and snapshot item details"""
        # Snapshot inventory details if new
        if not self.pk and self.inventory:
            self.item_name = self.inventory.item_name
            self.part_number = self.inventory.part_number
            self.warranty_period = self.inventory.warranty_period
            
            # Auto-set price from inventory if not provided
            if not self.unit_price or self.unit_price == Decimal('0.00'):
                # Use default retail pricing from inventory
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
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Do not deduct inventory at item creation; defer to delivery status
        # Recalculate order totals
        self.order.calculate_totals()
    
    def deduct_inventory(self):
        """Deduct quantity from inventory and mark as deducted"""
        if self.inventory_deducted:
            return
        if self.inventory.quantity < self.quantity:
            raise ValidationError(
                f"Insufficient stock for {self.item_name}. "
                f"Available: {self.inventory.quantity}, Required: {self.quantity}"
            )
        self.inventory.quantity -= self.quantity
        self.inventory.save(update_fields=['quantity', 'modified'])
        self.inventory_deducted = True
        self.save(update_fields=['inventory_deducted', 'modified'])
    
    def restore_inventory(self):
        """Restore quantity to inventory only if previously deducted"""
        if not self.inventory_deducted:
            return
        self.inventory.quantity += self.quantity
        self.inventory.save(update_fields=['quantity', 'modified'])
        self.inventory_deducted = False
        self.save(update_fields=['inventory_deducted', 'modified'])
    
    def __str__(self):
        return f"{self.order.order_number} - {self.item_name} x {self.quantity}"
