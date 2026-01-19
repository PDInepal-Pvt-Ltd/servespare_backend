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

    def clean(self):
        """Validate cart"""
        errors = {}

        if not self.user_id and not self.user:
            errors['user'] = 'User is required.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
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
        errors = {}

        if not self.cart_id and not self.cart:
            errors['cart'] = 'Cart is required.'

        if not self.inventory_id and not self.inventory:
            errors['inventory'] = 'Inventory item is required.'

        if self.quantity is None:
            errors['quantity'] = 'Quantity is required.'
        elif self.quantity <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'
        elif self.quantity > Decimal('999999.99'):
            errors['quantity'] = 'Quantity cannot exceed 999,999.99.'

        if self.price is None:
            errors['price'] = 'Price is required.'
        elif self.price < 0:
            errors['price'] = 'Price cannot be negative.'
        elif self.price > Decimal('999999.99'):
            errors['price'] = 'Price cannot exceed 999,999.99.'

        # Check if inventory has sufficient stock
        if self.inventory_id and self.quantity and self.inventory.quantity < self.quantity:
            errors['quantity'] = f'Insufficient stock. Only {self.inventory.quantity} available.'

        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Always mirror the current inventory selling price with fallbacks
        # retail_pricing > mrp > base price
        if not self.price or self.price == Decimal('0.00'):
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
