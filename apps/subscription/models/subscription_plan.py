from django.db import models
from apps.base.models import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Model to store subscription plan details
    """
    
    
    plan_name = models.CharField(max_length=255, unique=True)
    plan_price = models.DecimalField(max_digits=10, decimal_places=2)
    no_of_user = models.CharField(max_length=50, default='1')
    no_of_branch = models.CharField(max_length=50, default='1')
    no_of_product = models.CharField(max_length=50)

    class Meta:
        db_table = 'subscription_plan'
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
        ordering = ['plan_price']
    
    def __str__(self):
        return f"{self.plan_name} - ${self.plan_price}"

