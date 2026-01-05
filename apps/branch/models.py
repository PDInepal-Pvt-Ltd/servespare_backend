from django.db import models
from apps.base.models import BaseModel
from apps.base.managers import TenantManager

class Branch(BaseModel):
    """
    Model to store branch /business information
    """
    
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='branches'
    )
    branch_name = models.CharField(max_length=255 , unique=True)
    branch_code = models.CharField(max_length=50, unique=True)
    Address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    Email = models.EmailField(unique=True)
    
    objects = TenantManager()
    
    class Meta:
        ordering = ["branch_name"]
   
   
   