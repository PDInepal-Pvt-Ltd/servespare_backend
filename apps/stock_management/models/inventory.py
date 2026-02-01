from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class Inventory(BaseModel):
    """
    Model to store inventory items
    """
    CATEGORY_CHOICES = [
        ('local', 'Local'),
        ('original', 'Original'),
    ]
    
    VEHICLE_TYPE_CHOICES = [
        ('two_wheeler', 'Two Wheeler'),
        ('four_wheeler', 'Four Wheeler'),
    ]
    
    WARRANTY_PERIOD_CHOICES = [
        ('no_warranty', 'No Warranty'),
        ('1_month', '1 Month'),
        ('2_month', '2 Month'),
        ('3_month', '3 Month'),
        ('4_month', '4 Month'),
        ('5_month', '5 Month'),
        ('6_month', '6 Month'),
        ('9_month', '9 Month'),
        ('12_month', '12 Month'),
        ('24_month', '24 Month'),
    ]
    
    # Tenant Context
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory_items',
        help_text='Tenant that owns this inventory item'
    )

    # Basic Information
    item_name = models.CharField(
        max_length=255,
        help_text='Name of the inventory item'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        help_text='Category of the item'
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        help_text='Type of vehicle this part is for'
    )
    party = models.ForeignKey(
        'stock_management.Party',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_items',
        help_text='Party/Supplier associated with this item'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory_items',
        help_text='Branch that owns this inventory record'
    )
    
    # Part Information
    part_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Part number or SKU'
    )
    hsn_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='HSN (Harmonized System of Nomenclature) Code'
    )
    
    # Stock Information
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Current stock quantity'
    )
    min_stock_level = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Minimum stock level before reordering'
    )
    storage_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Storage location or warehouse location'
    )
    
    # Pricing Information
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Base price'
    )
    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Maximum Retail Price (MRP)'
    )
    
    # Three Tier Pricing
    retail_pricing = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Retail price'
    )
    wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Wholesale price'
    )
    distributor_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Distributor price'
    )
    
    # Warranty
    warranty_period = models.CharField(
        max_length=20,
        choices=WARRANTY_PERIOD_CHOICES,
        default='no_warranty',
        help_text='Warranty period for the item'
    )
    
    # Barcode
    barcode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text='Barcode for scanning (alphanumeric only, max 50 characters)'
    )
    
    # Primary Image for Inventory List
    image = models.ImageField(
        upload_to='inventory_images/',
        blank=True,
        null=True,
        help_text='Primary image for inventory item (shown in inventory list)'
    )
    
    # Vehicle Details Section
    vehicle_bike_details = models.TextField(
        blank=True,
        null=True,
        help_text='Vehicle/Bike details'
    )
    model = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Model name'
    )
    type = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Type of vehicle/part'
    )
    
    class Meta:
        db_table = 'inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'
        ordering = ['item_name']
        indexes = [
            models.Index(fields=['item_name']),
            models.Index(fields=['category']),
            models.Index(fields=['vehicle_type']),
            models.Index(fields=['part_number']),
            models.Index(fields=['barcode']),
            models.Index(fields=['tenant']),
            models.Index(fields=['branch']),
        ]

    objects = TenantManager()
    
    def clean(self):
        """Validate all fields"""
        errors = {}
        
        # Validate item_name
        if not self.item_name or not self.item_name.strip():
            errors['item_name'] = 'Item name is required.'
        elif len(self.item_name) < 2:
            errors['item_name'] = 'Item name must be at least 2 characters.'
        
        # Validate category
        if not self.category:
            errors['category'] = 'Category is required.'
        
        # Validate vehicle_type
        if not self.vehicle_type:
            errors['vehicle_type'] = 'Vehicle type is required.'
        
        # Validate part_number
        if self.part_number and len(self.part_number) < 2:
            errors['part_number'] = 'Part number must be at least 2 characters.'
        
        # Validate HSN code
        if self.hsn_code:
            if not self.hsn_code.isdigit():
                errors['hsn_code'] = 'HSN code must contain only digits.'
            elif len(self.hsn_code) != 8:
                errors['hsn_code'] = 'HSN code must be exactly 8 digits.'
        
        # Validate quantity
        if self.quantity < 0:
            errors['quantity'] = 'Quantity cannot be negative.'
        if self.quantity > 999999.99:
            errors['quantity'] = 'Quantity cannot exceed 999,999.99.'
        
        # Validate min_stock_level
        if self.min_stock_level < 0:
            errors['min_stock_level'] = 'Minimum stock level cannot be negative.'
        if self.min_stock_level > 999999.99:
            errors['min_stock_level'] = 'Minimum stock level cannot exceed 999,999.99.'
        
        # Validate storage_location
        if self.storage_location and len(self.storage_location) < 2:
            errors['storage_location'] = 'Storage location must be at least 2 characters.'
        
        # Validate prices
        for price_field in ['price', 'mrp', 'retail_pricing', 'wholesale_price', 'distributor_price']:
            value = getattr(self, price_field, Decimal('0.00'))
            if value < 0:
                errors[price_field] = f'{price_field.replace("_", " ").title()} cannot be negative.'
            if value > 999999.99:
                errors[price_field] = f'{price_field.replace("_", " ").title()} cannot exceed 999,999.99.'
        
        prices = {
            'distributor': self.distributor_price,
            'wholesale': self.wholesale_price,
            'retail': self.retail_pricing,
            'mrp': self.mrp,
        }
        
        # Check pricing hierarchy: Distributor < Wholesale < Retail < MRP
        if prices['distributor'] > 0 and prices['wholesale'] > 0:
            if prices['distributor'] >= prices['wholesale']:
                errors['distributor_price'] = 'Distributor price must be less than Wholesale price.'
        
        if prices['wholesale'] > 0 and prices['retail'] > 0:
            if prices['wholesale'] >= prices['retail']:
                errors['wholesale_price'] = 'Wholesale price must be less than Retail price.'
        
        if prices['retail'] > 0 and prices['mrp'] > 0:
            if prices['retail'] >= prices['mrp']:
                errors['retail_pricing'] = 'Retail price must be less than MRP.'
        
        # Validate barcode
        if self.barcode:
            # Check length
            if len(self.barcode) > 50:
                errors['barcode'] = 'Barcode cannot exceed 50 characters.'
            # Check if alphanumeric only (numbers and letters a-z, case-insensitive)
            elif not self.barcode.replace('-', '').replace('_', '').isalnum():
                errors['barcode'] = 'Barcode must contain only numbers and letters (a-z).'
        
        # Validate vehicle_bike_details
        if self.vehicle_bike_details and len(self.vehicle_bike_details) < 5:
            errors['vehicle_bike_details'] = 'Vehicle/Bike details must be at least 5 characters.'
        
        # Validate model
        if self.model and len(self.model) < 2:
            errors['model'] = 'Model must be at least 2 characters.'
        
        # Validate type
        if self.type and len(self.type) < 2:
            errors['type'] = 'Type must be at least 2 characters.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.quantity <= self.min_stock_level
    
    def __str__(self):
        return f"{self.item_name} ({self.get_category_display()}) - {self.get_vehicle_type_display()}"

    def get_default_selling_price(self):
        """Return preferred selling price with sensible fallbacks.

        Priority: retail_pricing > mrp > price > 0.00
        """
        from decimal import Decimal
        for value in (self.retail_pricing, self.mrp, self.price):
            try:
                if value is not None and value > 0:
                    return value
            except Exception:
                continue
        return Decimal('0.00')


class InventoryImage(BaseModel):
    """
    Model to store multiple images for inventory items
    """
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory_images',
        help_text='Tenant that owns this inventory image'
    )

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='images',
        help_text='Inventory item this image belongs to'
    )
    image = models.ImageField(
        upload_to='inventory_images/',
        help_text='Part image'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Optional description for the image'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory_images',
        help_text='Branch associated with this image'
    )
    
    class Meta:
        db_table = 'inventory_image'
        verbose_name = 'Inventory Image'
        verbose_name_plural = 'Inventory Images'
        ordering = ['created']

    objects = TenantManager()
    
    def clean(self):
        """Validate all fields"""
        errors = {}
        
        # Validate inventory
        if not self.inventory:
            errors['inventory'] = 'Inventory item is required.'
        
        # Validate image
        if not self.image:
            errors['image'] = 'Image is required.'
        else:
            # Check image file size (max 5MB)
            if self.image.size > 5242880:  # 5MB in bytes
                errors['image'] = 'Image size cannot exceed 5MB.'
        
        # Validate description
        if self.description and len(self.description) < 2:
            errors['description'] = 'Description must be at least 2 characters.'
        if self.description and len(self.description) > 255:
            errors['description'] = 'Description cannot exceed 255 characters.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Image for {self.inventory.item_name}"

