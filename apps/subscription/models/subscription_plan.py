from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from apps.base.models import BaseModel


class SubscriptionPlan(BaseModel):
    """
    Model to store subscription plan details
    """
    
    
    plan_name = models.CharField(
        max_length=255,
        unique=True,
        null=False,
        blank=False,
        help_text='Unique name for the subscription plan'
    )
    plan_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False,
        blank=False,
        validators=[MinValueValidator(0.01)],
        help_text='Price must be greater than 0'
    )
    no_of_user = models.CharField(
        max_length=50,
        default='1',
        null=False,
        blank=False,
        validators=[RegexValidator(regex=r'^\d+$|^unlimited$', message='Must be a positive number or "unlimited"')],
        help_text='Number of users allowed (number or "unlimited")'
    )
    no_of_branch = models.CharField(
        max_length=50,
        default='1',
        null=False,
        blank=False,
        validators=[RegexValidator(regex=r'^\d+$|^unlimited$', message='Must be a positive number or "unlimited"')],
        help_text='Number of branches allowed (number or "unlimited")'
    )
    no_of_product = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        validators=[RegexValidator(regex=r'^\d+$|^unlimited$', message='Must be a positive number or "unlimited"')],
        help_text='Number of products allowed (number or "unlimited")'
    )

    class Meta:
        db_table = 'subscription_plan'
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
        ordering = ['plan_price']
    
    def __str__(self):
        return f"{self.plan_name} - ${self.plan_price}"

