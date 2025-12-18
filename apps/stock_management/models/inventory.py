from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.base.models import BaseModel


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
        on_delete=models.SET_NULL,
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
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text='Barcode for scanning'
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
        ]
    
    def clean(self):
        """Validate pricing hierarchy: Distributor < Wholesale < Retail < MRP"""
        prices = {
            'distributor': self.distributor_price,
            'wholesale': self.wholesale_price,
            'retail': self.retail_pricing,
            'mrp': self.mrp,
        }
        
        # Check pricing hierarchy
        if prices['distributor'] > 0 and prices['wholesale'] > 0:
            if prices['distributor'] >= prices['wholesale']:
                raise ValidationError({
                    'distributor_price': 'Distributor price must be less than Wholesale price.'
                })
        
        if prices['wholesale'] > 0 and prices['retail'] > 0:
            if prices['wholesale'] >= prices['retail']:
                raise ValidationError({
                    'wholesale_price': 'Wholesale price must be less than Retail price.'
                })
        
        if prices['retail'] > 0 and prices['mrp'] > 0:
            if prices['retail'] >= prices['mrp']:
                raise ValidationError({
                    'retail_pricing': 'Retail price must be less than MRP.'
                })
        
        # Validate stock levels
        if self.min_stock_level < 0:
            raise ValidationError({
                'min_stock_level': 'Minimum stock level cannot be negative.'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.quantity <= self.min_stock_level
    
    def __str__(self):
        return f"{self.item_name} ({self.get_category_display()}) - {self.get_vehicle_type_display()}"


class InventoryImage(BaseModel):
    """
    Model to store multiple images for inventory items
    """
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
    is_primary = models.BooleanField(
        default=False,
        help_text='Mark as primary image'
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_images',
        help_text='Branch associated with this image'
    )
    
    class Meta:
        db_table = 'inventory_image'
        verbose_name = 'Inventory Image'
        verbose_name_plural = 'Inventory Images'
        ordering = ['-is_primary', 'created']
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images
        if self.is_primary:
            InventoryImage.objects.filter(
                inventory=self.inventory,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Image for {self.inventory.item_name}"

