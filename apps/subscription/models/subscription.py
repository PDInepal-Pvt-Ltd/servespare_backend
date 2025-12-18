from django.db import models
from django.core.exceptions import ValidationError
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


class Subscription(BaseModel):
    """
    Model to store tenant subscriptions to subscription plans
    """
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subscription_plan = models.ForeignKey(
        'subscription.SubscriptionPlan',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )

    subscription_date = models.DateField()
    finish_date = models.DateField()
    renew_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'subscription'
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['-subscription_date']
        unique_together = [['tenant', 'subscription_plan', 'subscription_date']]
    
    def clean(self):
        """Validate that finish_date is after subscription_date"""
        if self.finish_date and self.subscription_date:
            if self.finish_date <= self.subscription_date:
                raise ValidationError({
                    'finish_date': 'Finish date must be after subscription date.'
                })
        if self.renew_date and self.finish_date:
            if self.renew_date < self.finish_date:
                raise ValidationError({
                    'renew_date': 'Renew date should be on or after finish date.'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.tenant.business_name} - {self.subscription_plan.plan_name} ({self.subscription_date})"

    objects = TenantManager()

