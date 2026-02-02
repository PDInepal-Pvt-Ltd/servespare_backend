"""
Utility functions for role-based access control and permissions.

Provides helper functions to check user roles, permissions, and access levels.
"""

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


def is_super_admin(user):
    """
    Check if user is a Super Admin.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is Super Admin, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    from apps.users.models import User
    return user.role == User.Role.SUPER_ADMIN


def is_tenant_admin(user):
    """
    Check if user is a Tenant Admin.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is Tenant Admin with a valid tenant, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    from apps.users.models import User
    return user.role == User.Role.ADMIN and user.tenant is not None


def is_tenant_user(user):
    """
    Check if user is a Tenant User.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is Tenant User with a valid tenant, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    from apps.users.models import User
    return user.role == User.Role.SUB_ADMIN and user.tenant is not None


def is_customer(user):
    """
    Check if user is a Customer.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is Customer, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    from apps.users.models import User
    return user.role == User.Role.CUSTOMER


def can_access_tenant(user, tenant):
    """
    Check if user can access a specific tenant.
    
    Rules:
    - Super Admin: Can access all tenants
    - Tenant Admin: Can only access their own tenant
    - Tenant User: Can only access their own tenant (read-only)
    - Customer: Can access all tenants
    
    Args:
        user: Django User object
        tenant: Tenant object
        
    Returns:
        bool: True if user can access the tenant, False otherwise
    """
    if not user or not user.is_authenticated or not tenant:
        return False
    
    from apps.users.models import User
    
    # Super Admin and Customer can access all tenants
    if user.role in [User.Role.SUPER_ADMIN, User.Role.CUSTOMER]:
        return True
    
    # Tenant Admin and Tenant User can only access their own tenant
    if user.role in [User.Role.ADMIN, User.Role.SUB_ADMIN]:
        return user.tenant == tenant
    
    return False


def can_manage_tenant(user, tenant):
    """
    Check if user can manage (edit/delete) a specific tenant.
    
    Rules:
    - Super Admin: Can manage all tenants
    - Tenant Admin: Can only manage their own tenant
    - Others: Cannot manage tenants
    
    Args:
        user: Django User object
        tenant: Tenant object
        
    Returns:
        bool: True if user can manage the tenant, False otherwise
    """
    if not user or not user.is_authenticated or not tenant:
        return False
    
    from apps.users.models import User
    
    # Super Admin can manage all tenants
    if user.role == User.Role.SUPER_ADMIN:
        return True
    
    # Tenant Admin can only manage their own tenant
    if user.role == User.Role.ADMIN:
        return user.tenant == tenant
    
    return False


def can_manage_tenant_users(user, tenant):
    """
    Check if user can manage users in a specific tenant.
    
    Rules:
    - Super Admin: Can manage users in all tenants
    - Tenant Admin: Can only manage users in their own tenant
    - Others: Cannot manage users
    
    Args:
        user: Django User object
        tenant: Tenant object
        
    Returns:
        bool: True if user can manage users in the tenant, False otherwise
    """
    if not user or not user.is_authenticated or not tenant:
        return False
    
    from apps.users.models import User
    
    # Super Admin can manage users in all tenants
    if user.role == User.Role.SUPER_ADMIN:
        return True
    
    # Tenant Admin can only manage users in their own tenant
    if user.role == User.Role.ADMIN:
        return user.tenant == tenant
    
    return False


def can_manage_user(user, target_user):
    """
    Check if user can manage (edit/delete) a specific user.
    
    Rules:
    - Super Admin: Can manage all users
    - Tenant Admin: Can manage users in their own tenant
    - Tenant User: Can manage users in their own tenant
    - Cashier: Can delete (soft delete) any user
    - Inventory Manager: Can delete (soft delete) any user
    - Customer: Can delete (soft delete) any user
    
    Args:
        user: Django User object (the one performing the action)
        target_user: Django User object (the one being managed)
        
    Returns:
        bool: True if user can manage the target user, False otherwise
    """
    if not user or not user.is_authenticated or not target_user:
        return False
    
    from apps.users.models import User
    
    # Super Admin can manage all users
    if user.role == User.Role.SUPER_ADMIN:
        return True
    
    # Tenant Admin can manage users in their own tenant
    if user.role == User.Role.ADMIN:
        return target_user.tenant == user.tenant
    
    # Tenant User can manage users in their own tenant
    if user.role == User.Role.SUB_ADMIN:
        return target_user.tenant == user.tenant
    
    # Cashier, Inventory Manager, and Customer can delete any user (soft delete)
    if user.role in [User.Role.CASHIER, User.Role.INVENTORY_MANAGER, User.Role.CUSTOMER]:
        return True
    
    return False


def get_tenant_queryset_for_user(user, queryset):
    """
    Filter queryset based on user's role and tenant access.
    
    Rules:
    - Super Admin: Get all objects (no filtering)
    - Customer: Get all objects (no filtering)
    - Tenant Admin: Get only objects from their tenant
    - Tenant User: Get only objects from their tenant (if applicable)
    
    Args:
        user: Django User object
        queryset: Django QuerySet to filter
        
    Returns:
        QuerySet: Filtered queryset based on user permissions
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    from apps.users.models import User
    
    # Super Admin and Customer can see all objects
    if user.role in [User.Role.SUPER_ADMIN, User.Role.CUSTOMER]:
        return queryset
    
    # Tenant Admin and Tenant User can only see their tenant's objects
    if user.role in [User.Role.ADMIN, User.Role.SUB_ADMIN]:
        if user.tenant:
            # Try to filter by tenant if the model has a tenant field
            if hasattr(queryset.model, 'tenant'):
                return queryset.filter(tenant=user.tenant)
        return queryset.none()
    
    return queryset.none()


def is_inventory_manager(user):
    """
    Check if user is an Inventory Manager.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is Inventory Manager with a valid branch, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    from apps.users.models import User
    return user.role == User.Role.INVENTORY_MANAGER and user.branch is not None


def is_cashier(user):
    """
    Check if user is a Cashier.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user is Cashier with a valid branch, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    from apps.users.models import User
    return user.role == User.Role.CASHIER and user.branch is not None


def can_manage_branch(user, branch):
    """
    Check if user can manage a specific branch.
    
    Rules:
    - Super Admin: Can manage all branches
    - Tenant Admin: Can manage branches in their tenant
    - Inventory Manager: Can manage only their assigned branch
    - Cashier: Can manage only their assigned branch
    
    Args:
        user: Django User object
        branch: Branch object
        
    Returns:
        bool: True if user can manage the branch, False otherwise
    """
    if not user or not user.is_authenticated or not branch:
        return False
    
    from apps.users.models import User
    
    # Super Admin can manage all branches
    if user.role == User.Role.SUPER_ADMIN:
        return True
    
    # Tenant Admin can manage branches in their tenant
    if user.role == User.Role.ADMIN:
        return branch.tenant == user.tenant
    
    # Inventory Manager and Cashier can only manage their assigned branch
    if user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
        return user.branch == branch
    
    return False


def can_manage_branch_resources(user, branch):
    """
    Check if user can manage resources in a specific branch.
    
    Rules:
    - Super Admin: Can manage all resources in all branches
    - Tenant Admin: Can manage resources in all branches of their tenant
    - Inventory Manager: Can manage inventory resources in their branch
    - Cashier: Can manage cash/transaction resources in their branch
    
    Args:
        user: Django User object
        branch: Branch object
        
    Returns:
        bool: True if user can manage branch resources, False otherwise
    """
    if not user or not user.is_authenticated or not branch:
        return False
    
    from apps.users.models import User
    
    # Super Admin can manage all resources
    if user.role == User.Role.SUPER_ADMIN:
        return True
    
    # Tenant Admin can manage resources in all branches of their tenant
    if user.role == User.Role.ADMIN:
        return branch.tenant == user.tenant
    
    # Inventory Manager and Cashier can manage resources in their branch
    if user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
        return user.branch == branch
    
    return False


def get_branch_queryset_for_user(user, queryset):
    """
    Filter queryset based on user's role and branch access.
    
    Rules:
    - Super Admin: Get all objects (no filtering)
    - Tenant Admin: Get objects from all branches in their tenant
    - Inventory Manager: Get objects from their branch
    - Cashier: Get objects from their branch
    - Others: No access
    
    Args:
        user: Django User object
        queryset: Django QuerySet to filter
        
    Returns:
        QuerySet: Filtered queryset based on user permissions
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    
    from apps.users.models import User
    
    # Super Admin can see all objects
    if user.role == User.Role.SUPER_ADMIN:
        return queryset
    
    # Tenant Admin can see objects from all branches in their tenant
    if user.role == User.Role.ADMIN:
        if user.tenant and hasattr(queryset.model, 'branch'):
            from django.db.models import Q
            from apps.branch.models import Branch
            tenant_branches = Branch.objects.filter(tenant=user.tenant).values_list('id', flat=True)
            return queryset.filter(
                Q(branch__in=tenant_branches) | Q(branch__isnull=True, tenant=user.tenant)
            )
        return queryset.none()
    
    # Inventory Manager and Cashier can only see their branch's objects
    if user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
        if user.branch and hasattr(queryset.model, 'branch'):
            return queryset.filter(branch=user.branch)
        return queryset.none()
    
    return queryset.none()


def check_permission_or_raise(permission_func, user, *args, **kwargs):
    """
    Check permission using a permission function and raise PermissionDenied if False.
    
    Args:
        permission_func: A callable that returns a boolean
        user: Django User object
        *args, **kwargs: Arguments to pass to the permission function
        
    Raises:
        PermissionDenied: If permission check fails
    """
    if not permission_func(user, *args, **kwargs):
        raise PermissionDenied(_('You do not have permission to perform this action.'))


class RolePermissionMixin:
    """
    Mixin for views to apply role-based access control.
    
    Subclasses should define:
    - `permission_classes`: List of permission classes to apply
    - `role_permission_map`: Dict mapping roles to allowed operations (optional)
    """
    
    def check_permissions(self, request):
        """Override to apply additional role-based checks."""
        super().check_permissions(request)
        
        # Additional role-specific checks can be added here
        if request.user and request.user.is_authenticated:
            self.perform_role_check(request)
    
    def perform_role_check(self, request):
        """
        Override this method in subclasses to add custom role checks.
        
        Args:
            request: HTTP request object
        """
        pass
