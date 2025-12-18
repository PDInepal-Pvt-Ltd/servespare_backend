from django.db import models
from model_utils.models import TimeStampedModel
from django.core.exceptions import ValidationError


class Favorite(TimeStampedModel):
    """
    Model to manage favorite products for customers/users
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text='User who added this to favorites'
    )
    inventory = models.ForeignKey(
        'stock_management.Inventory',
        on_delete=models.CASCADE,
        related_name='favorited_by',
        help_text='Inventory product added to favorites'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this favorite is still active'
    )
    
    class Meta:
        db_table = 'favorites'
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        ordering = ['-created']
        unique_together = [['user', 'inventory']]
        indexes = [
            models.Index(fields=['user', 'inventory']),
            models.Index(fields=['user', '-created']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.inventory.item_name}"
    
    def clean(self):
        """Validate favorite entry"""
        # Check if this product is already in user's favorites
        existing = Favorite.objects.filter(
            user=self.user,
            inventory=self.inventory,
            is_active=True
        ).exclude(pk=self.pk).exists()
        
        if existing:
            raise ValidationError(
                'This product is already in your favorites.'
            )
    
    @classmethod
    def add_to_favorites(cls, user, inventory):
        """
        Add product to user's favorites with duplicate checking
        
        Args:
            user: User instance
            inventory: Inventory instance
        
        Returns:
            tuple: (favorite_instance, created, message)
        """
        # Check if already exists
        existing = cls.objects.filter(
            user=user,
            inventory=inventory,
            is_active=True
        ).first()
        
        if existing:
            return (existing, False, f"'{inventory.item_name}' is already in your favorites.")
        
        # Check if exists but marked inactive
        inactive = cls.objects.filter(
            user=user,
            inventory=inventory,
            is_active=False
        ).first()
        
        if inactive:
            # Reactivate the existing entry
            inactive.is_active = True
            inactive.save()
            return (inactive, True, f"'{inventory.item_name}' added back to your favorites.")
        
        # Create new favorite
        favorite = cls.objects.create(
            user=user,
            inventory=inventory,
            is_active=True
        )
        return (favorite, True, f"'{inventory.item_name}' added to your favorites.")
    
    @classmethod
    def remove_from_favorites(cls, user, inventory):
        """
        Remove product from user's favorites
        
        Args:
            user: User instance
            inventory: Inventory instance
        
        Returns:
            tuple: (success, message)
        """
        favorite = cls.objects.filter(
            user=user,
            inventory=inventory,
            is_active=True
        ).first()
        
        if not favorite:
            return (False, f"'{inventory.item_name}' is not in your favorites.")
        
        favorite.is_active = False
        favorite.save()
        return (True, f"'{inventory.item_name}' removed from your favorites.")
