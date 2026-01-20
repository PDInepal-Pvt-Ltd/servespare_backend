from django.db import models
from django.core.exceptions import ValidationError
from datetime import date
from apps.base.models import BaseModel
from apps.base.managers import TenantManager


def no_past_date(value):
    """Validator to ensure date is not in the past"""
    if value < date.today():
        raise ValidationError('Date cannot be in the past.')


class Subscription(BaseModel):
    """
    Model to store tenant subscriptions to subscription plans
    """
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        null=False,
        blank=False,
        help_text='Tenant subscribed to the plan'
    )
    subscription_plan = models.ForeignKey(
        'subscription.SubscriptionPlan',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        null=False,
        blank=False,
        help_text='Subscription plan associated'
    )

    subscription_date = models.DateField(
        null=False,
        blank=False,
        validators=[no_past_date],
        help_text='Date when subscription starts (cannot be in the past)'
    )
    finish_date = models.DateField(
        null=False,
        blank=False,
        validators=[no_past_date],
        help_text='Date when subscription ends (cannot be in the past)'
    )
    
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
      
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.tenant.business_name} - {self.subscription_plan.plan_name} ({self.subscription_date})"

    objects = TenantManager()

