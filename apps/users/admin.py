from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.base.admin import TenantAdminMixin
from .models import User


@admin.register(User)
class UserAdmin(TenantAdminMixin, BaseUserAdmin):
    """Admin interface for custom User model."""
    
    # Display configuration
    list_display = [
        'username', 'email', 'full_name', 'role', 'status', 'branch', 'is_staff', 
        'is_active', 'two_factor_enabled', 'tenant', 'workspace_id', 'created', 'last_login_at'
    ]
    list_filter = [
        'role', 'status', 'branch', 'is_staff', 'is_superuser', 'is_active', 'tenant',
        'must_change_password', 'two_factor_enabled', 'groups', 'created'
    ]
    search_fields = [
        'username', 'email', 'full_name', 'phone', 'tenant__name', 'branch__branch_name',
        'branch__branch_code', 'workspace_id'
    ]
    ordering = ['-created']
    readonly_fields = ['created', 'modified', 'last_login_at', 'last_login', 'date_joined', 'is_removed']
    
    # Fieldsets for detail view
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('full_name', 'first_name', 'last_name', 'phone', 'avatar')
        }),
        (_('Workspace & Tenant'), {
            'fields': ('tenant', 'branch', 'workspace_id',)
        }),
        (_('Role & Status'), {
            'fields': ('role', 'status', 'is_active', 'must_change_password', 'two_factor_enabled')
        }),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'last_login_at', 'date_joined', 'created', 'modified'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'is_removed'),
            'classes': ('collapse',)
        }),
    )
    
    # Fieldsets for add view
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('Personal Info'), {
            'fields': ('full_name', 'phone')
        }),
        (_('Workspace & Tenant'), {
            'fields': ('tenant', 'branch', 'workspace_id')
        }),
        (_('Role & Status'), {
            'fields': ('role', 'status', 'is_active', 'is_staff', 'is_superuser')
        }),
    )
    
    # Actions
    actions = ['activate_users', 'deactivate_users', 'suspend_users']
    
    def activate_users(self, request, queryset):
        """Bulk activate selected users."""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'{updated} user(s) activated successfully.')
    activate_users.short_description = _('Activate selected users')
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate selected users."""
        updated = queryset.update(status='inactive', is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated successfully.')
    deactivate_users.short_description = _('Deactivate selected users')
    
    def suspend_users(self, request, queryset):
        """Bulk suspend selected users."""
        updated = queryset.update(status='suspended', is_active=False)
        self.message_user(request, f'{updated} user(s) suspended successfully.')
    suspend_users.short_description = _('Suspend selected users')
    
    def has_delete_permission(self, request, obj=None):
        """
        Allow all authenticated users with specific roles to delete (soft delete) users.
        
        Roles with delete permission:
        - SUPER_ADMIN: Can delete any user
        - ADMIN: Can delete users in their tenant
        - SUB_ADMIN: Can delete users in their tenant
        - CASHIER: Can soft delete any user
        - INVENTORY_MANAGER: Can soft delete any user
        - CUSTOMER: Can soft delete any user
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # If checking specific object permission
        if obj:
            from apps.base.permission_utils import can_manage_user
            return can_manage_user(request.user, obj)
        
        # For general delete permission (list view)
        # All users with these roles can access delete functionality
        allowed_roles = [
            User.Role.SUPER_ADMIN,
            User.Role.ADMIN,
            User.Role.SUB_ADMIN,
            User.Role.CASHIER,
            User.Role.INVENTORY_MANAGER,
            User.Role.CUSTOMER
        ]
        return request.user.role in allowed_roles
    
    def get_readonly_fields(self, request, obj=None):
        """Make tenant field readonly when editing existing users, except for superadmins."""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Editing an existing user
            # Only superadmins can change tenant
            if not request.user.is_superuser:
                readonly.append('tenant')
        return readonly
