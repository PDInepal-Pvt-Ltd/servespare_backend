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
    
    Customers have read-only access to products and can manage their own cart/orders.
    """
    message = _('Only Customer users can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role == User.Role.CUSTOMER
        )
    
    def has_object_permission(self, request, view, obj):
        """
        Customers can only view objects, not modify them.
        Exception: can modify their own user profile, cart, and orders.
        """
        from apps.users.models import User
        from apps.carts.models import Cart, CartItem
        
        # Customers can access their own user profile
        if isinstance(obj, User):
            return obj == request.user
        
        # Customers can manage their own cart and cart items
        if isinstance(obj, Cart):
            return obj.user == request.user
        
        if isinstance(obj, CartItem):
            return obj.cart.user == request.user
        
        # For all other objects, only allow read operations
        return request.method in permissions.SAFE_METHODS


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
    
    Super Admin has full access.
    Customer has read-only access to public resources.
    """
    message = _('Only Super Admin or Customer can access this resource.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        return request.user.role in [User.Role.SUPER_ADMIN, User.Role.CUSTOMER]
    
    def has_object_permission(self, request, view, obj):
        """
        Super Admin can do everything.
        Customer can only read objects.
        """
        from apps.users.models import User
        
        # Super Admin has full access
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Customer has read-only access
        if request.user.role == User.Role.CUSTOMER:
            return request.method in permissions.SAFE_METHODS
        
        return False


class CanViewInventory(permissions.BasePermission):
    """
    Permission for viewing inventory (products).
    
    - Super Admin, Tenant Admin, Inventory Manager: Full access to manage inventory
    - Customer: Read-only access to view products
    """
    message = _('You do not have permission to access inventory.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        # If unauthenticated, deny here. Public read-only access is handled
        # by view-level logic when no Authorization header is present.
        if not (request.user and request.user.is_authenticated):
            return False

        # Super Admin, Tenant Admin, Inventory Manager can manage inventory
        if request.user.role in [User.Role.SUPER_ADMIN, User.Role.ADMIN, User.Role.INVENTORY_MANAGER]:
            return True

        # Cashier and Customer: read-only access
        if request.user.role in [User.Role.CASHIER, User.Role.CUSTOMER]:
            return request.method in permissions.SAFE_METHODS

        return False

    def has_object_permission(self, request, view, obj):
        """
        Object-level permissions:
        - Super Admin: full access
        - Tenant Admin: can modify/delete objects in their tenant
        - Inventory Manager: can modify/delete objects in their branch
        - Cashier/Customer: read-only
        """
        from apps.users.models import User
        from apps.base.permission_utils import can_manage_tenant, can_manage_branch_resources

        if request.user.role == User.Role.SUPER_ADMIN:
            return True

        # Read-only for safe methods
        if request.method in permissions.SAFE_METHODS:
            return True

        # Tenant Admin: modify if they manage tenant or branch belongs to their tenant
        if request.user.role == User.Role.ADMIN:
            if can_manage_tenant(request.user, getattr(obj, 'tenant', None)):
                return True
            if can_manage_branch_resources(request.user, getattr(obj, 'branch', None)):
                return True

        # Inventory Manager: modify if branch matches
        if request.user.role == User.Role.INVENTORY_MANAGER:
            if can_manage_branch_resources(request.user, getattr(obj, 'branch', None)):
                return True

        return False


class CanViewOwnOrders(permissions.BasePermission):
    """
    Permission for managing orders and bills.
    
    - Super Admin, Tenant Admin, Branch Manager: Full access to all orders
    - Cashier: Can create and manage bills in their assigned branch
    - Customer: Full CRUD access to their own orders only
    """
    message = _('You do not have permission to access this order.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Management roles have full access
        if request.user.role in [User.Role.SUPER_ADMIN, User.Role.ADMIN, User.Role.SUB_ADMIN]:
            return True
        
        # Cashier can create and manage bills in their branch
        if request.user.role == User.Role.CASHIER:
            return request.user.branch is not None
        
        # Customers can create and manage their own orders
        if request.user.role == User.Role.CUSTOMER:
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Check object-level permissions for orders.
        """
        from apps.users.models import User
        
        # Super Admin has full access
        if request.user.role == User.Role.SUPER_ADMIN:
            return True
        
        # Tenant Admin can access their tenant's orders
        if request.user.role == User.Role.ADMIN:
            if hasattr(obj, 'tenant'):
                return obj.tenant == request.user.tenant
        
        # Sub Admin can access their branch's orders
        if request.user.role == User.Role.SUB_ADMIN:
            if hasattr(obj, 'branch'):
                return obj.branch == request.user.branch
        
        # Cashier can access bills in their branch
        if request.user.role == User.Role.CASHIER:
            if hasattr(obj, 'branch'):
                return obj.branch == request.user.branch
        
        # Customers can manage their own orders
        if request.user.role == User.Role.CUSTOMER:
            if hasattr(obj, 'customer'):
                return obj.customer == request.user
        
        return False


class CanManageTenantUsers(permissions.BasePermission):
    """
    Permission to manage users in a tenant.
    
    Super Admin can manage all users.
    Tenant Admin can manage users in their own tenant.
    Tenant User can manage users in their own tenant.
    All authenticated users can delete (soft delete).
    """
    message = _('You do not have permission to manage users in this tenant.')
    
    def has_permission(self, request, view):
        from apps.users.models import User
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        # All authenticated users can perform actions
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can manage the specific user object.
        All authenticated users can delete (soft delete).
        """
        from apps.users.models import User as UserModel
        
        # All authenticated users can manage (delete) users
        return True


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
