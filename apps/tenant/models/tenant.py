from django.db import models
from django.core.validators import RegexValidator, EmailValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
import re
from apps.base.models import BaseModel


class Tenant(BaseModel):
    """
    Model to store tenant/business information
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Phone number validator - allows formats like +977-9841234567, 9841234567, +977 9841234567
    phone_validator = RegexValidator(
        regex=r'^\+?[0-9]{1,4}?[-.\s]?\(?[0-9]{1,3}?\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}$',
        message="Phone number must be entered in a valid format. E.g., '+977-9841234567' or '9841234567'"
    )
    
    # PAN number validator - exactly 9 digits, numeric only
    pan_validator = RegexValidator(
        regex=r'^[0-9]{9}$',
        message="PAN number must be exactly 9 digits (numeric only)"
    )
    
    # Province validator - only letters, spaces, and hyphens
    province_validator = RegexValidator(
        regex=r'^[a-zA-Z\s-]+$',
        message="Province name can only contain letters, spaces, and hyphens"
    )
    
    # District validator - only letters, spaces, and hyphens
    district_validator = RegexValidator(
        regex=r'^[a-zA-Z\s-]+$',
        message="District name can only contain letters, spaces, and hyphens"
    )
    
    business_name = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(2, message="Business name must be at least 2 characters long")],
        help_text="Name of the business/tenant"
    )
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(message="Enter a valid email address")],
        help_text="Business email address (must be unique)"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_validator],
        help_text="Contact phone number"
    )
    pan_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[pan_validator],
        help_text="PAN/Tax registration number"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[MinLengthValidator(3, message="Location must be at least 3 characters long")],
        help_text="Business location/address"
    )
    province = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[
            MinLengthValidator(2, message="Province name must be at least 2 characters long"),
            province_validator
        ],
        help_text="Province/State where business is located"
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[
            MinLengthValidator(2, message="District name must be at least 2 characters long"),
            district_validator
        ],
        help_text="District/County where business is located"
    )
    package = models.ForeignKey(
        'subscription.SubscriptionPlan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenants',
        help_text="Subscription plan for this tenant"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        help_text="Current status of the tenant"
    )
    
    class Meta:
        db_table = 'tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created']
    
    def __str__(self):
        return f"{self.business_name} ({self.email})"
    
    def clean(self):
        """Custom model validation"""
        super().clean()
        errors = {}
        
        # Validate business name
        if self.business_name:
            self.business_name = self.business_name.strip()
            if not self.business_name:
                errors['business_name'] = 'Business name cannot be empty or just whitespace'
            elif len(self.business_name) < 2:
                errors['business_name'] = 'Business name must be at least 2 characters long'
            elif len(self.business_name) > 255:
                errors['business_name'] = 'Business name cannot exceed 255 characters'
        
        # Validate and normalize email
        if self.email:
            self.email = self.email.lower().strip()
            # Check email uniqueness
            queryset = Tenant.objects.filter(email=self.email)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                errors['email'] = 'A tenant with this email already exists'
        
        # Validate phone number if provided
        if self.phone:
            self.phone = self.phone.strip()
            if self.phone:
                phone_pattern = r'^\+?[0-9]{1,4}?[-.\s]?\(?[0-9]{1,3}?\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}$'
                if not re.match(phone_pattern, self.phone):
                    errors['phone'] = "Phone number must be in a valid format. E.g., '+977-9841234567' or '9841234567'"
        
        # Validate PAN number if provided
        if self.pan_number:
            self.pan_number = self.pan_number.strip()
            if self.pan_number:
                pan_pattern = r'^[0-9]{9}$'
                if not re.match(pan_pattern, self.pan_number):
                    errors['pan_number'] = 'PAN number must be exactly 9 digits (numeric only, no letters or special characters)'
        
        # Validate location if provided
        if self.location:
            self.location = self.location.strip()
            if self.location:
                if len(self.location) < 3:
                    errors['location'] = 'Location must be at least 3 characters long'
                elif len(self.location) > 255:
                    errors['location'] = 'Location cannot exceed 255 characters'
        
        # Validate province if provided
        if self.province:
            self.province = self.province.strip().title()
            if self.province:
                if len(self.province) < 2:
                    errors['province'] = 'Province name must be at least 2 characters long'
                elif len(self.province) > 100:
                    errors['province'] = 'Province name cannot exceed 100 characters'
                elif not re.match(r'^[a-zA-Z\s-]+$', self.province):
                    errors['province'] = 'Province name can only contain letters, spaces, and hyphens'
        
        # Validate district if provided
        if self.district:
            self.district = self.district.strip().title()
            if self.district:
                if len(self.district) < 2:
                    errors['district'] = 'District name must be at least 2 characters long'
                elif len(self.district) > 100:
                    errors['district'] = 'District name cannot exceed 100 characters'
                elif not re.match(r'^[a-zA-Z\s-]+$', self.district):
                    errors['district'] = 'District name can only contain letters, spaces, and hyphens'
        
        # Cross-field validation: If district is provided, province should also be provided
        if self.district and not self.province:
            errors['province'] = 'Province is required when district is specified'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override save to run full_clean before saving"""
        self.full_clean()
        super().save(*args, **kwargs)
    
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

