from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from model_utils.models import TimeStampedModel


class Cart(TimeStampedModel):
    """
    Shopping cart for customers
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='cart',
        help_text='User who owns this cart'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this cart is active'
    )
    
    class Meta:
        db_table = 'carts'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'
        ordering = ['-created']
    
    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return self.items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
    
    @property
    def subtotal(self):
        """Calculate subtotal of all items in cart"""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.total_price
        return total


class CartItem(TimeStampedModel):
    """
    Individual items in a cart
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Cart this item belongs to'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this cart item is active'
    )
    inventory = models.ForeignKey(
        'stock_management.Inventory',
        on_delete=models.CASCADE,
        related_name='cart_items',
        help_text='Inventory item'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Quantity of this item'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price at the time of adding to cart'
    )
    
    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        ordering = ['-created']
        unique_together = [['cart', 'inventory']]
        indexes = [
            models.Index(fields=['cart', 'inventory']),
            models.Index(fields=['created']),
        ]
    
    def clean(self):
        """Validate cart item"""
        if self.quantity <= 0:
            raise ValidationError({
                'quantity': 'Quantity must be greater than zero.'
            })
        
        # Check if inventory has sufficient stock
        if self.inventory.quantity < self.quantity:
            raise ValidationError({
                'quantity': f'Insufficient stock. Only {self.inventory.quantity} available.'
            })
    
    def save(self, *args, **kwargs):
        # Always mirror the current inventory selling price with fallbacks
        # retail_pricing > mrp > base price
        self.price = self.inventory.get_default_selling_price()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def total_price(self):
        """Calculate total price for this item"""
        if self.price is None:
            # Gracefully handle unsaved admin forms where price is not set yet
            return Decimal('0.00') if self.quantity is None else self.quantity * Decimal('0.00')
        return self.quantity * self.price
    
    def __str__(self):
        return f"{self.quantity}x {self.inventory.item_name} in {self.cart.user.username}'s cart"
