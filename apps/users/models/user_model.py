from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from apps.base.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User model extending Django's AbstractUser with additional fields.
    
    Uses role field for role management with Groups sync.
    Inherits from BaseModel for timestamps and soft delete functionality.
    
    Roles available: Super Admin, Admin, Sub Admin, Cashier, Inventory Manager, Customer
    """
    
    # Role choices
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', _('Super Admin')
        ADMIN = 'admin', _('Admin')
        SUB_ADMIN = 'sub_admin', _('Sub_Admin')
        CASHIER = 'cashier', _('Cashier')
        INVENTORY_MANAGER = 'inventory_manager', _('Inventory Manager')
        CUSTOMER = 'customer', _('Customer')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
    
    # Email field (not unique, username is used for login)
    email = models.EmailField(
        _('email address'),
        blank=True,
        null=True,
        db_index=True,
        help_text=_('Email address for the user.')
    )
    
    # Role field
    role = models.CharField(
        _('role'),
        max_length=30,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
        help_text=_('User role determining access level and permissions.')
    )
    
    # Contact information
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Contact phone number.')
    )
    
    location = models.CharField(
        _('location'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('User location or address.')
    )
    
    # Personal information
    full_name = models.CharField(
        _('full name'),
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Full name of the user.')
    )
    
    # User status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text=_('Current status of the user account.')
    )
    
    must_change_password = models.BooleanField(
        _('must change password'),
        default=True,
        help_text=_('Indicates if the user must change their password on next login.')
    )
    
    last_login_at = models.DateTimeField(
        _('last login at'),
        null=True,
        blank=True,
        help_text=_('Timestamp of the last successful login.')
    )
    
    # Profile
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('Profile avatar image.')
    )
    
    # Workspace and creator tracking
    workspace_id = models.CharField(
        _('workspace ID'),
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Workspace identifier for multi-tenancy.')
    )
    
    tenant = models.ForeignKey(
        'tenant.Tenant',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        db_column='tenant_id',
        verbose_name=_('tenant'),
        help_text=_('Tenant organization this user belongs to.')
    )

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text=_('Branch this user belongs to.')
    )
    
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name=_('created by'),
        help_text=_('User who created this account.')
    )
    
    # Use username for authentication
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']  # Required fields for createsuperuser command
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['email'], name='users_email_idx'),
            models.Index(fields=['status', 'is_active'], name='users_status_active_idx'),
            models.Index(fields=['workspace_id', 'status'], name='users_workspace_status_idx'),
            models.Index(fields=['created'], name='users_created_idx'),
        ]
    
    def __str__(self):
        """String representation of the user."""
        return self.username
    
    def get_full_name(self):
        """Return the full name or username if full name is not set."""
        return self.full_name or self.username
    
    def get_short_name(self):
        """Return the short name (first name) or username."""
        return self.first_name or self.username
    
    def is_account_active(self):
        """Check if the user account is active and not soft deleted."""
        return self.status == self.Status.ACTIVE and self.is_active and not self.is_removed
    
    def suspend_account(self):
        """Suspend the user account."""
        self.status = self.Status.SUSPENDED
        self.is_active = False
        self.save(update_fields=['status', 'is_active', 'modified'])
    
    def activate_account(self):
        """Activate the user account."""
        self.status = self.Status.ACTIVE
        self.is_active = True
        self.save(update_fields=['status', 'is_active', 'modified'])
    
    def deactivate_account(self):
        """Deactivate the user account."""
        self.status = self.Status.INACTIVE
        self.is_active = False
        self.save(update_fields=['status', 'is_active', 'modified'])
    
    def update_last_login(self):
        """Update the last login timestamp."""
        from django.utils import timezone
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at', 'modified'])
    
    def has_workspace(self):
        """Check if the user belongs to a workspace."""
        return bool(self.workspace_id)
    
    def get_role(self):
        """Get the user's role."""
        return self.get_role_display()
    
    def get_role_value(self):
        """Get the user's role value."""
        return self.role
    
    def is_super_admin(self):
        """Check if user is a Super Admin."""
        return self.is_superuser or self.role == self.Role.SUPER_ADMIN
    
    def is_admin(self):
        """Check if user is an Admin."""
        return self.role == self.Role.ADMIN or self.is_super_admin()
    
    def is_cashier(self):
        """Check if user is a Cashier."""
        return self.role == self.Role.CASHIER
    
    def is_inventory_manager(self):
        """Check if user is an Inventory Manager."""
        return self.role == self.Role.INVENTORY_MANAGER
    
    def is_customer(self):
        """Check if user is a Customer."""
        return self.role == self.Role.CUSTOMER
    
    def set_role(self, role_value):
        """Set user role and sync with corresponding group."""
        if role_value in [choice[0] for choice in self.Role.choices]:
            self.role = role_value
            self.save(update_fields=['role', 'modified'])
            self._sync_role_to_group()
            return True
        return False
    
    def _sync_role_to_group(self):
        """Sync role field to corresponding Django group."""
        # Clear existing groups
        self.groups.clear()
        
        # Add group based on role
        role_name = self.get_role_display()
        group, created = Group.objects.get_or_create(name=role_name)
        self.groups.add(group)
    
    def save(self, *args, **kwargs):
        """Override save to sync role with groups and handle customer-specific behavior."""
        is_new = self.pk is None
        
        # Handle customer role specific behavior
        if self.role == self.Role.CUSTOMER:
            self.must_change_password = False
            self.tenant = None
        
        super().save(*args, **kwargs)
        
        # Sync role to group after save
        if is_new or 'role' in kwargs.get('update_fields', []):
            self._sync_role_to_group()


@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    """
    Signal to create default user groups with appropriate permissions after migration.
    This ensures role-based access control groups are available.
    """
    if sender.name == 'apps.users':
        from django.contrib.contenttypes.models import ContentType
        
        # Define roles and their permissions (using display names)
        roles_permissions = {
            'Super Admin': {
                'description': 'Full system access with all permissions',
                'permissions': 'all'  # Will get all permissions
            },
            'Admin': {
                'description': 'Administrative access to manage users and settings',
                'permissions': [
                    ('add_user', 'users', 'user'),
                    ('change_user', 'users', 'user'),
                    ('delete_user', 'users', 'user'),
                    ('view_user', 'users', 'user'),
                ]
            },
            'Cashier': {
                'description': 'Access to sales and customer transactions',
                'permissions': [
                    ('view_user', 'users', 'user'),  # Can view users
                    # Add more cashier-specific permissions here
                ]
            },
            'Inventory Manager': {
                'description': 'Manage inventory, stock, and suppliers',
                'permissions': [
                    ('view_user', 'users', 'user'),  # Can view users
                    # Add more inventory-specific permissions here
                ]
            },
            'Customer': {
                'description': 'Customer account with basic access',
                'permissions': [
                    ('view_user', 'users', 'user'),  # Can view their own user
                    # Add more customer-specific permissions here
                ]
            },
        }
        
        for role_name, role_config in roles_permissions.items():
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created or not group.permissions.exists():
                if role_config['permissions'] == 'all':
                    # Super Admin gets all permissions
                    all_permissions = Permission.objects.all()
                    group.permissions.set(all_permissions)
                else:
                    # Add specific permissions
                    permissions = []
                    for perm_codename, app_label, model_name in role_config['permissions']:
                        try:
                            content_type = ContentType.objects.get(
                                app_label=app_label,
                                model=model_name
                            )
                            permission = Permission.objects.get(
                                codename=perm_codename,
                                content_type=content_type
                            )
                            permissions.append(permission)
                        except (ContentType.DoesNotExist, Permission.DoesNotExist):
                            pass
                    
                    group.permissions.set(permissions)
                
                print(f"✓ Created/Updated group: {role_name} - {role_config['description']}")
