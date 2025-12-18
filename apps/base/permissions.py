"""
Role-based permission classes for DRF.

Defines permission classes for different user roles:
- Super Admin: Access everything
- Tenant Admin: Manage own tenant and its users
- Tenant User: View own tenant and admin (read-only)
- Customer: Access all resources like super admin
"""

from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission class for Super Admin access only.
    
    Super Admin can access everything in the system.
    """
    message = _('Only Super Admin users can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.SUPER_ADMIN
        )


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission class for Tenant Admin access.
    
    Tenant Admin can manage only their own tenant and its users.
    """
    message = _('Only Tenant Admin users can perform this action.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.ADMIN
            and request.user.tenant is not None
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is the admin of the tenant containing the object.
        """
        from apps.tenant.models import Tenant
        
        # If object is a Tenant, check if it's the user's tenant
        if isinstance(obj, Tenant):
            return obj == request.user.tenant
        
        # If object has a tenant attribute, check if it matches user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        # If object has a created_by attribute (User), check tenant
        if hasattr(obj, 'created_by') and isinstance(obj.created_by, type(request.user)):
            return obj.created_by.tenant == request.user.tenant
        
        return False


class IsCustomer(permissions.BasePermission):
    """
    Permission class for Customer access.
    
    Customers have access like Super Admin (all resources).
    """
    message = _('Only Customer users can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.CUSTOMER
        )


class IsTenantUser(permissions.BasePermission):
    """
    Permission class for Tenant User access.
    
    Tenant Users can only view their own tenant and admin information (read-only).
    """
    message = _('Tenant users can only view their own tenant information.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.SUB_ADMIN
            and request.user.tenant is not None
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Only allow access to own tenant and read-only operations.
        """
        from apps.tenant.models import Tenant
        
        # Only read operations allowed
        if request.method not in permissions.SAFE_METHODS:
            return False
        
        # If object is a Tenant, check if it's the user's tenant
        if isinstance(obj, Tenant):
            return obj == request.user.tenant
        
        # If object has a tenant attribute, check if it matches user's tenant
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.user.tenant
        
        return False


class IsSuperAdminOrTenantAdmin(permissions.BasePermission):
    """
    Permission for Super Admin or Tenant Admin.
    
    Super Admin can do everything globally.
    Tenant Admin can manage only their own tenant.
    """
    message = _('Only Super Admin or Tenant Admin can perform this action.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Super Admin has all permissions
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin must have a tenant assigned
        if request.user.role == User.Role.ADMIN:
            return request.user.tenant is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Super Admin can access everything.
        Tenant Admin can only access their own tenant data.
        """
        from apps.users.models import User
        from apps.tenant.models import Tenant
        
        # Super Admin can access everything
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can only access their own tenant's data
        if request.user.role == User.Role.ADMIN:
            if isinstance(obj, Tenant):
                return obj == request.user.tenant
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            if hasattr(obj, 'created_by') and hasattr(obj.created_by, 'tenant'):
                return obj.created_by.tenant == request.user.tenant
        
        return False


class IsSuperAdminOrCustomer(permissions.BasePermission):
    """
    Permission for Super Admin or Customer.
    
    Both have full access to all resources.
    """
    message = _('Only Super Admin or Customer can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.role in [User.Role.SUPER_ADMIN, User.Role.CUSTOMER]


class CanManageTenantUsers(permissions.BasePermission):
    """
    Permission to manage users in a tenant.
    
    Super Admin can manage all users.
    Tenant Admin can only manage users in their own tenant.
    """
    message = _('You do not have permission to manage users in this tenant.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Super Admin can manage all users
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can manage users in their tenant
        if request.user.role == User.Role.ADMIN:
            return request.user.tenant is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can manage the specific user object.
        """
        from apps.users.models import User as UserModel
        from apps.tenant.models import Tenant
        
        # Super Admin can manage all users
        if request.user.role == UserModel.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can only manage users in their own tenant
        if request.user.role == UserModel.Role.ADMIN:
            if isinstance(obj, UserModel):
                return obj.tenant == request.user.tenant
        
        return False


class CanEditTenantDetails(permissions.BasePermission):
    """
    Permission to edit tenant details.
    
    Super Admin can edit all tenant details.
    Tenant Admin can only edit their own tenant details.
    """
    message = _('You do not have permission to edit this tenant.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Super Admin can edit all tenant details
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can edit their own tenant
        if request.user.role == User.Role.ADMIN:
            return request.user.tenant is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can edit the specific tenant object.
        """
        from apps.users.models import User
        from apps.tenant.models import Tenant
        
        # Super Admin can edit all tenant details
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can only edit their own tenant
        if request.user.role == User.Role.ADMIN:
            if isinstance(obj, Tenant):
                return obj == request.user.tenant
        
        return False


class IsInventoryManager(permissions.BasePermission):
    """
    Permission class for Inventory Manager access.
    
    Inventory Manager can manage inventory/stock in their assigned branch.
    """
    message = _('Only Inventory Manager users can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.INVENTORY_MANAGER
            and request.user.branch is not None
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Check if inventory manager's branch matches the object's branch.
        """
        # If object has a branch attribute, check if it matches user's branch
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch
        
        # If object has tenant and the user's branch belongs to that tenant
        if hasattr(obj, 'tenant') and hasattr(request.user, 'branch'):
            if request.user.branch and request.user.branch.tenant == obj.tenant:
                return True
        
        return False


class IsCashier(permissions.BasePermission):
    """
    Permission class for Cashier access.
    
    Cashier can manage cash/bank transactions in their assigned branch.
    """
    message = _('Only Cashier users can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.CASHIER
            and request.user.branch is not None
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Check if cashier's branch matches the object's branch.
        """
        # If object has a branch attribute, check if it matches user's branch
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch
        
        # If object has tenant and the user's branch belongs to that tenant
        if hasattr(obj, 'tenant') and hasattr(request.user, 'branch'):
            if request.user.branch and request.user.branch.tenant == obj.tenant:
                return True
        
        return False


class CanManageBranchResources(permissions.BasePermission):
    """
    Permission for managing branch-level resources.
    
    - Super Admin: Can manage all branch resources globally
    - Tenant Admin: Can manage resources in all branches of their tenant
    - Inventory Manager: Can manage inventory in their branch
    - Cashier: Can manage transactions in their branch
    """
    message = _('You do not have permission to manage branch resources.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Super Admin can manage all branch resources
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can manage branch resources in their tenant
        if request.user.role == User.Role.ADMIN:
            return request.user.tenant is not None
        
        # Inventory Manager and Cashier must have a branch assigned
        if request.user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
            return request.user.branch is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can manage the specific branch resource.
        """
        from apps.users.models import User
        
        # Super Admin can manage all resources
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can manage resources in their tenant's branches
        if request.user.role == User.Role.ADMIN:
            if hasattr(obj, 'branch'):
                return obj.branch.tenant == request.user.tenant
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            return False
        
        # Inventory Manager and Cashier can only manage their own branch
        if request.user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
            if hasattr(obj, 'branch'):
                return obj.branch == request.user.branch
            return False
        
        return False


class IsSuperAdminOrTenantAdminOrBranchManager(permissions.BasePermission):
    """
    Permission for Super Admin, Tenant Admin, Inventory Manager, or Cashier.
    
    Each can manage resources at their respective level.
    """
    message = _('You do not have permission to perform this action.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Super Admin can manage everything
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin must have a tenant
        if request.user.role == User.Role.ADMIN:
            return request.user.tenant is not None
        
        # Inventory Manager and Cashier must have a branch
        if request.user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
            return request.user.branch is not None
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions.
        """
        from apps.users.models import User
        
        # Super Admin can access everything
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can access their tenant's data
        if request.user.role == User.Role.ADMIN:
            if hasattr(obj, 'branch'):
                return obj.branch.tenant == request.user.tenant
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
            return False
        
        # Inventory Manager and Cashier can access their branch's data
        if request.user.role in [User.Role.INVENTORY_MANAGER, User.Role.CASHIER]:
            if hasattr(obj, 'branch'):
                return obj.branch == request.user.branch
            return False
        
        return False
