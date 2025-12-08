from django.db import models
from apps.base.models import BaseModel


class Tenant(BaseModel):
    """
    Model to store tenant/business information
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
    ]
    
    business_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    package = models.ForeignKey(
        'subscription.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenants'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial'
    )
    
    class Meta:
        db_table = 'tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.business_name} ({self.email})"

