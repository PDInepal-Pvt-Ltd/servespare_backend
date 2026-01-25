from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager
import uuid

# Nepal Province-District Mapping
NEPAL_PROVINCE_DISTRICTS = {
    'Koshi': ['Bhojpur', 'Dhankuta', 'Ilam', 'Jhapa', 'Khotang', 'Morang', 'Okhaldhunga', 'Panchthar', 'Sankhuwasabha', 'Solukhumbu', 'Sunsari', 'Taplejung', 'Terhathum', 'Udayapur'],
    'Madhesh': ['Bara', 'Dhanusha', 'Mahottari', 'Parsa', 'Rautahat', 'Saptari', 'Sarlahi', 'Siraha'],
    'Bagmati': ['Bhaktapur', 'Chitwan', 'Dhading', 'Dolakha', 'Kathmandu', 'Kavrepalanchok', 'Lalitpur', 'Makwanpur', 'Nuwakot', 'Ramechhap', 'Rasuwa', 'Sindhuli', 'Sindhupalchok'],
    'Gandaki': ['Baglung', 'Gorkha', 'Kaski', 'Lamjung', 'Manang', 'Mustang', 'Myagdi', 'Nawalpur', 'Parbat', 'Syangja', 'Tanahun'],
    'Lumbini': ['Arghakhanchi', 'Banke', 'Bardiya', 'Dang', 'Gulmi', 'Kapilvastu', 'Palpa', 'Pyuthan', 'Rolpa', 'Rupandehi', 'Rukum East', 'Nawalparasi West'],
    'Karnali': ['Dailekh', 'Dolpa', 'Humla', 'Jajarkot', 'Jumla', 'Kalikot', 'Mugu', 'Rukum West', 'Salyan', 'Surkhet'],
    'Sudurpashchim': ['Achham', 'Baitadi', 'Bajhang', 'Bajura', 'Dadeldhura', 'Darchula', 'Doti', 'Kailali', 'Kanchanpur'],
}


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
    delivery_province = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Delivery province'
    )
    delivery_district = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Delivery district'
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
        self.full_clean()
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
        
        # Subtotal should be pre-tax: sum of (qty * unit_price - item-level discount)
        pretax_subtotal = Decimal('0.00')
        for item in items:
            quantity = item.quantity or Decimal('0.00')
            unit_price = item.unit_price or Decimal('0.00')
            item_discount = item.discount_amount or Decimal('0.00')
            line_pretax = (quantity * unit_price) - item_discount
            if line_pretax < 0:
                line_pretax = Decimal('0.00')
            pretax_subtotal += line_pretax

        self.subtotal = pretax_subtotal.quantize(Decimal('0.01'))

        # Calculate discount based on order-level percentage
        if self.discount_percentage and self.discount_percentage > 0:
            self.discount_amount = ((self.subtotal * self.discount_percentage) / Decimal('100.00')).quantize(Decimal('0.01'))
        else:
            self.discount_amount = Decimal('0.00')
        
        # Calculate amount after discount
        amount_after_discount = self.subtotal - self.discount_amount
        
        # Ensure tax percentage defaults to 13% if not provided
        self.tax_percentage = self.tax_percentage or Decimal('13.00')

        # Calculate tax
        if self.tax_percentage > 0:
            tax_value = (amount_after_discount * self.tax_percentage) / Decimal('100.00')
            self.tax_amount = tax_value.quantize(Decimal('0.01'))
        else:
            self.tax_amount = Decimal('0.00')
        
        # Calculate total
        shipping = self.shipping_charges or Decimal('0.00')
        self.total_amount = (amount_after_discount + self.tax_amount + shipping).quantize(Decimal('0.01'))
        
        self.save(update_fields=[
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount', 
            'modified'
        ])

    def clean(self):
        errors = {}

        if not self.customer_id and not self.customer:
            errors['customer'] = 'Customer is required.'

        if not self.order_status:
            errors['order_status'] = 'Order status is required.'
        elif self.order_status not in dict(self.ORDER_STATUS_CHOICES):
            errors['order_status'] = 'Invalid order status.'

        if not self.delivery_address or not self.delivery_address.strip():
            errors['delivery_address'] = 'Delivery address is required.'
        elif len(self.delivery_address.strip()) < 5:
            errors['delivery_address'] = 'Delivery address must be at least 5 characters.'

        if not self.delivery_city or not self.delivery_city.strip():
            errors['delivery_city'] = 'Delivery city is required.'
        elif len(self.delivery_city.strip()) > 100:
            errors['delivery_city'] = 'Delivery city cannot exceed 100 characters.'

        if self.delivery_province and len(self.delivery_province.strip()) > 100:
            errors['delivery_province'] = 'Delivery province cannot exceed 100 characters.'
        elif self.delivery_province and self.delivery_province not in NEPAL_PROVINCE_DISTRICTS:
            errors['delivery_province'] = f'Invalid province. Must be one of: {", ".join(NEPAL_PROVINCE_DISTRICTS.keys())}'

        if self.delivery_district and len(self.delivery_district.strip()) > 100:
            errors['delivery_district'] = 'Delivery district cannot exceed 100 characters.'
        elif self.delivery_district and self.delivery_province:
            # Validate that district belongs to selected province
            valid_districts = NEPAL_PROVINCE_DISTRICTS.get(self.delivery_province, [])
            if self.delivery_district not in valid_districts:
                errors['delivery_district'] = f'Invalid district for {self.delivery_province}. Must be one of: {", ".join(valid_districts)}'
        elif self.delivery_district and not self.delivery_province:
            errors['delivery_district'] = 'Delivery province must be selected when specifying a district.'

        if self.delivery_pincode and len(self.delivery_pincode.strip()) > 20:
            errors['delivery_pincode'] = 'Delivery pincode cannot exceed 20 characters.'

        if self.tracking_number and len(self.tracking_number.strip()) > 100:
            errors['tracking_number'] = 'Tracking number cannot exceed 100 characters.'

        if self.courier_partner and len(self.courier_partner.strip()) > 100:
            errors['courier_partner'] = 'Courier partner cannot exceed 100 characters.'

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

        if self.subtotal is not None and self.discount_amount is not None:
            if self.discount_amount > self.subtotal:
                errors['discount_amount'] = 'Discount amount cannot exceed subtotal.'

        if self.total_amount is not None and self.total_amount < Decimal('0.00'):
            errors['total_amount'] = 'Total amount cannot be negative.'

        if errors:
            raise ValidationError(errors)
    
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
        """Generate invoice from this sales order with all current items"""
        from apps.sales.models import Invoice, InvoiceItem
        
        # Check if invoice already exists
        if hasattr(self, 'invoice'):
            invoice = self.invoice
        else:
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
        
        # Create or update invoice items from order items
        # First, get existing invoice item IDs for order items
        existing_invoice_items = set(
            InvoiceItem.objects.filter(
                invoice=invoice,
                sales_order_item__isnull=False
            ).values_list('sales_order_item_id', flat=True)
        )
        
        # Create items for order items that don't have invoice items yet
        for order_item in self.items.all():
            if order_item.id not in existing_invoice_items:
                InvoiceItem.objects.create(
                    tenant=self.tenant,
                    invoice=invoice,
                    sales_order_item=order_item,
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
        
        # Update invoice totals from order
        invoice.subtotal = self.subtotal
        invoice.discount_percentage = self.discount_percentage
        invoice.discount_amount = self.discount_amount
        invoice.tax_percentage = self.tax_percentage
        invoice.tax_amount = self.tax_amount
        invoice.shipping_charges = self.shipping_charges
        invoice.total_amount = self.total_amount
        invoice.save(update_fields=[
            'subtotal', 'discount_percentage', 'discount_amount',
            'tax_percentage', 'tax_amount', 'shipping_charges', 'total_amount'
        ])
        
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
        
        self.full_clean()

        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Do not deduct inventory at item creation; defer to delivery status
        # Recalculate order totals
        self.order.calculate_totals()

    def clean(self):
        errors = {}

        if not self.order_id and not self.order:
            errors['order'] = 'Order is required.'

        if not self.inventory_id and not self.inventory:
            errors['inventory'] = 'Inventory item is required.'

        if not self.item_name or not self.item_name.strip():
            errors['item_name'] = 'Item name is required.'
        elif len(self.item_name.strip()) > 255:
            errors['item_name'] = 'Item name cannot exceed 255 characters.'

        if self.part_number and len(self.part_number.strip()) > 100:
            errors['part_number'] = 'Part number cannot exceed 100 characters.'

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

        # Validate inventory quantity availability
        if self.inventory_id and self.inventory:
            if self.quantity and self.quantity > self.inventory.quantity:
                errors['quantity'] = (
                    f'Insufficient inventory for {self.item_name}. '
                    f'Available: {self.inventory.quantity}, Requested: {self.quantity}'
                )

        if errors:
            raise ValidationError(errors)
    
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
