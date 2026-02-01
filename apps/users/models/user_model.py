from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import (
    MinLengthValidator,
    FileExtensionValidator,
    validate_email
)
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
import re

from apps.base.models import BaseModel
from apps.base.managers import TenantManager


# Custom Validators
def validate_phone_number(value):
    """
    Validate Nepali phone number format.
    Accepts:
    - Mobile: 10 digits starting with 97 or 98 (e.g., 9841234567)
    - Landline: 6-8 digits with area code (e.g., 01-4445678)
    - International format: +977 followed by mobile/landline
    - Formats accepted: with/without spaces, hyphens, parentheses
    """
    if not value:
        return
    
    # Remove common separators for validation
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Check for international format (+977)
    if cleaned.startswith('+977'):
        cleaned = cleaned[4:]  # Remove +977
    elif cleaned.startswith('977'):
        cleaned = cleaned[3:]  # Remove 977
    
    # Must contain only digits after cleaning
    if not cleaned.isdigit():
        raise ValidationError(
            _('Phone number must contain only digits, spaces, hyphens, parentheses, or +977 for international format.'),
            code='invalid_phone_format'
        )
    
    # Validate based on number type
    if len(cleaned) == 10:
        # Mobile number validation (must start with 97 or 98)
        if not (cleaned.startswith('97') or cleaned.startswith('98')):
            raise ValidationError(
                _('Nepali mobile number must start with 97 or 98.'),
                code='invalid_mobile_prefix'
            )
    elif len(cleaned) >= 6 and len(cleaned) <= 8:
        # Landline number (6-8 digits)
        # Valid - no additional prefix validation needed for landlines
        pass
    else:
        raise ValidationError(
            _('Phone number must be either 10 digits (mobile) or 6-8 digits (landline).'),
            code='invalid_phone_length'
        )


def validate_full_name(value):
    """
    Validate full name contains only valid name characters.
    Allows: letters (any language), spaces, hyphens, apostrophes, periods.
    """
    if not value:
        return
    
    # Strip whitespace for validation
    stripped_value = value.strip()
    
    # Minimum length check
    if len(stripped_value) < 2:
        raise ValidationError(
            _('Full name must be at least 2 characters long.'),
            code='name_too_short'
        )
    
    # Maximum length check
    if len(stripped_value) > 255:
        raise ValidationError(
            _('Full name cannot exceed 255 characters.'),
            code='name_too_long'
        )
    
    # Allow Unicode letters, spaces, hyphens, apostrophes, and periods
    # This pattern supports international names
    if not re.match(r"^[\w\s\-\'\.']+$", stripped_value, re.UNICODE):
        raise ValidationError(
            _('Full name can only contain letters, spaces, hyphens, apostrophes, and periods.'),
            code='invalid_name_characters'
        )
    
    # Prevent names with only special characters or spaces
    if not re.search(r'[a-zA-Z]', stripped_value):
        raise ValidationError(
            _('Full name must contain at least one letter.'),
            code='name_no_letters'
        )


def validate_username_chars(value):
    """
    Validate username contains only allowed characters.
    Allows: letters, numbers, hyphens, underscores, and periods.
    """
    if not value:
        return
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
        raise ValidationError(
            _('Username can only contain letters, numbers, hyphens, underscores, and periods.'),
            code='invalid_username'
        )
    
    # Username cannot start or end with special characters
    if not value[0].isalnum() or not value[-1].isalnum():
        raise ValidationError(
            _('Username must start and end with a letter or number.'),
            code='invalid_username_boundaries'
        )
    
    # Prevent consecutive special characters
    if re.search(r'[_.-]{2,}', value):
        raise ValidationError(
            _('Username cannot contain consecutive special characters.'),
            code='consecutive_special_chars'
        )


def validate_workspace_id(value):
    """
    Validate workspace ID format.
    Must be alphanumeric with optional hyphens and underscores.
    """
    if not value:
        return
    
    # Format validation
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', value):
        raise ValidationError(
            _('Workspace ID must start and end with alphanumeric characters and can contain hyphens or underscores.'),
            code='invalid_workspace_id'
        )
    
    # Length constraints
    if len(value) < 3:
        raise ValidationError(
            _('Workspace ID must be at least 3 characters long.'),
            code='workspace_id_too_short'
        )
    
    if len(value) > 100:
        raise ValidationError(
            _('Workspace ID cannot exceed 100 characters.'),
            code='workspace_id_too_long'
        )


def validate_location(value):
    """
    Validate location/address field.
    Must be at least 3 characters and not contain control characters.
    """
    if not value:
        return
    
    # Strip whitespace
    stripped_value = value.strip()
    
    # Minimum length
    if len(stripped_value) < 3:
        raise ValidationError(
            _('Location must be at least 3 characters long.'),
            code='location_too_short'
        )
    
    # Check for control characters
    if re.search(r'[\x00-\x1F\x7F]', value):
        raise ValidationError(
            _('Location contains invalid control characters.'),
            code='invalid_location_characters'
        )


def validate_avatar_size(value):
    """
    Validate avatar file size.
    Maximum size: 5MB
    """
    if not value:
        return
    
    filesize = value.size
    max_size_mb = 5
    max_size_bytes = max_size_mb * 1024 * 1024  # 5MB in bytes
    
    if filesize > max_size_bytes:
        raise ValidationError(
            _('Avatar file size cannot exceed %(max_size)s MB. Current size: %(current_size)s MB.') % {
                'max_size': max_size_mb,
                'current_size': round(filesize / (1024 * 1024), 2)
            },
            code='file_too_large'
        )


def validate_avatar_dimensions(value):
    """
    Validate avatar image dimensions.
    Maximum: 2000x2000 pixels, Minimum: 50x50 pixels
    """
    if not value:
        return
    
    try:
        from PIL import Image
        img = Image.open(value)
        width, height = img.size
        
        # Minimum dimensions
        if width < 50 or height < 50:
            raise ValidationError(
                _('Avatar image must be at least 50x50 pixels. Current size: %(width)sx%(height)s pixels.') % {
                    'width': width,
                    'height': height
                },
                code='image_too_small'
            )
        
        # Maximum dimensions
        if width > 2000 or height > 2000:
            raise ValidationError(
                _('Avatar image cannot exceed 2000x2000 pixels. Current size: %(width)sx%(height)s pixels.') % {
                    'width': width,
                    'height': height
                },
                code='image_too_large'
            )
    except ImportError:
        # PIL not installed, skip dimension validation
        pass
    except Exception:
        raise ValidationError(
            _('Invalid image file.'),
            code='invalid_image'
        )


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
    
    # Email field (unique, username is used for login)
    email = models.EmailField(
        _('email address'),
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        validators=[validate_email],
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
        unique=True,
        validators=[validate_phone_number],
        db_index=True,
        help_text=_('Contact phone number.')
    )
    
    location = models.CharField(
        _('location'),
        max_length=255,
        null=True,
        validators=[validate_location],
        blank=True,
        help_text=_('User location or address.')
    )
    
    # Personal information
    full_name = models.CharField(
        _('full name'),
        max_length=255,
        null=True,
        validators=[validate_full_name],
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
    
    two_factor_enabled = models.BooleanField(
        _('two factor authentication enabled'),
        default=False,
        help_text=_('Indicates if two-factor authentication is enabled for this user account.')
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
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                message=_('Only JPG, JPEG, PNG, GIF, and WEBP images are allowed.')
            ),
            validate_avatar_size,
            validate_avatar_dimensions,
        ],
        help_text=_('Profile avatar image. Max size: 5MB. Allowed formats: JPG, PNG, GIF, WEBP. Min: 50x50px, Max: 2000x2000px.')
    )
    
    # Workspace and creator tracking
    workspace_id = models.CharField(
        _('workspace ID'),
        max_length=100,
        null=True,
        validators=[validate_workspace_id],
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

    objects = TenantManager()

    branch = models.ForeignKey(
        'branch.Branch',
        on_delete=models.CASCADE,
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
    
    # Override username from AbstractUser to add validators
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        validators=[
            MinLengthValidator(3, _('Username must be at least 3 characters long.')),
            validate_username_chars,
        ],
        error_messages={
            'unique': _('A user with this username already exists.'),
        },
        help_text=_('Required. 3-150 characters. Letters, digits, hyphens, underscores, and periods only.'),
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
    
    def clean(self):
        """
        Model-level validation for cross-field validation and business rules.
        Called automatically during form validation and manually via full_clean().
        Validates business logic that spans multiple fields.
        """
        super().clean()
        errors = {}
        
        # Username validation (additional to field validators)
        if self.username:
            # Check for reserved usernames
            reserved_usernames = ['admin', 'root', 'system', 'api', 'www', 'ftp', 'mail', 'support']
            if self.username.lower() in reserved_usernames:
                errors['username'] = ValidationError(
                    _('This username is reserved and cannot be used.'),
                    code='reserved_username'
                )
        
        # Email validation - required for non-customer/non-super-admin roles
        if self.role not in [self.Role.CUSTOMER, self.Role.SUPER_ADMIN]:
            if not self.email:
                errors['email'] = ValidationError(
                    _('Email is required for %(role)s users.') % {'role': self.get_role_display()},
                    code='email_required'
                )
        
        # Validate email uniqueness (case-insensitive) - only if email is provided
        if self.email:
            # Normalize email
            self.email = self.email.lower().strip()
            
            # Check for duplicates
            email_qs = User.objects.filter(email__iexact=self.email)
            if self.pk:
                email_qs = email_qs.exclude(pk=self.pk)
            
            if email_qs.exists():
                errors['email'] = ValidationError(
                    _('A user with this email address already exists.'),
                    code='duplicate_email'
                )
        
        # Validate phone uniqueness - only if phone is provided
        if self.phone:
            phone_qs = User.objects.filter(phone=self.phone)
            if self.pk:
                phone_qs = phone_qs.exclude(pk=self.pk)
            
            if phone_qs.exists():
                errors['phone'] = ValidationError(
                    _('A user with this phone number already exists.'),
                    code='duplicate_phone'
                )
        
        # Role-tenant validation
        if self.role in [self.Role.SUPER_ADMIN, self.Role.CUSTOMER]:
            # Super Admins and Customers should not have a tenant
            if self.tenant:
                errors['tenant'] = ValidationError(
                    _('%(role)s users cannot be assigned to a tenant.') % {'role': self.get_role_display()},
                    code='invalid_tenant_for_role'
                )
        else:
            # All other roles must have a tenant
            if not self.tenant:
                errors['tenant'] = ValidationError(
                    _('%(role)s users must be assigned to a tenant.') % {'role': self.get_role_display()},
                    code='tenant_required'
                )
        
        # Branch-tenant consistency validation
        if self.branch:
            if not self.tenant:
                errors['branch'] = ValidationError(
                    _('Cannot assign a branch without a tenant.'),
                    code='branch_without_tenant'
                )
            elif self.branch.tenant_id != self.tenant_id:
                errors['branch'] = ValidationError(
                    _('Branch must belong to the same tenant as the user.'),
                    code='branch_tenant_mismatch'
                )
        
        # Status-is_active consistency validation
        if self.status == self.Status.SUSPENDED:
            if self.is_active:
                errors['is_active'] = ValidationError(
                    _('Suspended users must have is_active set to False.'),
                    code='suspended_user_active'
                )
        
        if self.status == self.Status.INACTIVE:
            if self.is_active:
                errors['is_active'] = ValidationError(
                    _('Inactive users must have is_active set to False.'),
                    code='inactive_user_active'
                )
        
        # Validate created_by
        if self.created_by:
            # Prevent circular reference
            if self.pk and self.created_by.pk == self.pk:
                errors['created_by'] = ValidationError(
                    _('User cannot be their own creator.'),
                    code='self_created'
                )
            
            # Creator should be from same tenant (except for super admins)
            if self.tenant and self.created_by.tenant:
                if self.tenant_id != self.created_by.tenant_id:
                    errors['created_by'] = ValidationError(
                        _('Creator must be from the same tenant.'),
                        code='creator_different_tenant'
                    )
        
        # Workspace ID validation with tenant
        if self.workspace_id and self.tenant:
            # Ensure workspace_id is consistent with tenant
            # Add specific business logic here if needed
            pass
        
        # Raise all validation errors at once
        if errors:
            raise ValidationError(errors)
    
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
    
    def set_password(self, raw_password):
        """
        Override set_password to include password validation.
        Validates password strength before setting.
        """
        if raw_password:
            # Validate password strength
            try:
                validate_password(raw_password, self)
            except ValidationError as e:
                raise ValidationError({'password': e.messages})
        
        super().set_password(raw_password)
    
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
        
        # Handle customer/super_admin role specific behavior
        # Customers and Super Admins created programmatically should not be forced
        # to change password on first login by default.
        if self.role == self.Role.CUSTOMER:
            self.must_change_password = False
            self.tenant = None
        elif self.role == self.Role.SUPER_ADMIN:
            self.must_change_password = False
        
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
        
        # Pre-fetch reusable permission sets
        view_permissions = list(Permission.objects.filter(codename__startswith='view_'))

        def resolve_permissions(permission_specs):
            """Resolve (codename, app_label, model) tuples into Permission objects."""
            resolved = []
            for perm_codename, app_label, model_name in permission_specs:
                try:
                    content_type = ContentType.objects.get(app_label=app_label, model=model_name)
                    permission = Permission.objects.get(codename=perm_codename, content_type=content_type)
                    resolved.append(permission)
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    continue
            return resolved

        # Define roles and their permissions (using display names)
        roles_permissions = {
            User.Role.SUPER_ADMIN.label: {
                'description': 'Full system access with all permissions',
                'permissions': 'all',
            },
            User.Role.ADMIN.label: {
                'description': 'Administrative access to manage users and settings',
                'permissions': view_permissions + resolve_permissions([
                    ('add_user', 'users', 'user'),
                    ('change_user', 'users', 'user'),
                    ('delete_user', 'users', 'user'),
                    ('view_user', 'users', 'user'),
                ]),
            },
            User.Role.SUB_ADMIN.label: {
                'description': 'Read-only access within tenant scope',
                'permissions': view_permissions,
            },
            User.Role.CASHIER.label: {
                'description': 'Access to sales and customer transactions (read + cashier ops)',
                'permissions': view_permissions + resolve_permissions([
                    ('view_user', 'users', 'user'),
                ]),
            },
            User.Role.INVENTORY_MANAGER.label: {
                'description': 'Manage inventory, stock, and suppliers',
                'permissions': view_permissions + resolve_permissions([
                    ('view_user', 'users', 'user'),
                ]),
            },
            User.Role.CUSTOMER.label: {
                'description': 'Customer account with read access across models',
                'permissions': view_permissions,
            },
        }

        for role_name, role_config in roles_permissions.items():
            group, _ = Group.objects.get_or_create(name=role_name)

            if role_config['permissions'] == 'all':
                permissions = Permission.objects.all()
            else:
                permissions = role_config['permissions']

            group.permissions.set(permissions)
            print(f"✓ Synced group: {role_name} - {role_config['description']}")
