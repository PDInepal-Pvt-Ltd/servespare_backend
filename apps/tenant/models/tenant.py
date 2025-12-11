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
    
    def get_user_count(self):
        """Get the total number of active users for this tenant"""
        return self.users.filter(is_active=True, is_removed=False).count()
    
    def get_allowed_users(self):
        """Get the number of users allowed by the current subscription plan"""
        if self.package:
            return self.package.no_of_user
        return 0
    
    def can_add_user(self):
        """Check if tenant can add more users based on subscription plan limit"""
        if not self.package:
            return False
        return self.get_user_count() < self.get_allowed_users()
    
    def get_remaining_user_slots(self):
        """Get the number of remaining user slots available"""
        if not self.package:
            return 0
        remaining = self.get_allowed_users() - self.get_user_count()
        return max(0, remaining)
    
    def get_admins(self):
        """Get all admin users (Admin and Super Admin) for this tenant"""
        from apps.users.models import User
        return self.users.filter(
            role__in=[User.Role.ADMIN, User.Role.SUPER_ADMIN],
            is_active=True,
            is_removed=False
        )
    
    def get_admin_count(self):
        """Get the count of admin users for this tenant"""
        return self.get_admins().count()
    
    def get_primary_admin(self):
        """Get the primary admin (first created admin) for this tenant"""
        return self.get_admins().order_by('created').first()
    
    def get_all_users_by_role(self):
        """Get a dictionary of all users grouped by role"""
        from apps.users.models import User
        users_by_role = {}
        for role_choice in User.Role.choices:
            role_value, role_label = role_choice
            users_by_role[role_label] = self.users.filter(
                role=role_value,
                is_active=True,
                is_removed=False
            ).count()
        return users_by_role

