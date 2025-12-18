# Role-Based Access Control (RBAC) System

## Overview

This system implements comprehensive role-based access control with multi-level permissions:
- **Super Admin**: Full system access
- **Tenant Admin**: Manage entire tenant and its users/branches
- **Inventory Manager**: Manage inventory in assigned branch
- **Cashier**: Manage cash transactions in assigned branch
- **Tenant User (Sub Admin)**: View-only access to own tenant
- **Customer**: Full system access (like Super Admin)

---

## User Roles & Permissions

### 1. Super Admin
- **Access Level**: Global (entire system)
- **Capabilities**:
  - View, create, update, delete all tenants
  - Manage all users across all tenants
  - Manage all branches
  - Manage all inventory items
  - Manage all transactions
  - No restrictions on any resource

### 2. Tenant Admin
- **Access Level**: Tenant-wide
- **Requires**: Must have `tenant` assigned
- **Capabilities**:
  - View and edit their own tenant details
  - Cannot delete tenants
  - Create and manage users within their tenant only
  - Manage all branches of their tenant
  - Manage inventory across all tenant branches
  - Manage transactions across all tenant branches
  - Cannot manage users/resources from other tenants

### 3. Inventory Manager
- **Access Level**: Branch-specific
- **Requires**: Must have `branch` assigned
- **Capabilities**:
  - View and manage inventory items in their assigned branch only
  - Create/update/delete inventory items in their branch
  - Cannot manage inventory from other branches
  - Read-only access to other modules

### 4. Cashier
- **Access Level**: Branch-specific
- **Requires**: Must have `branch` assigned
- **Capabilities**:
  - View and manage cash transactions in their assigned branch only
  - Create/update/delete transactions in their branch
  - Cannot manage transactions from other branches
  - Read-only access to other modules

### 5. Sub Admin (Tenant User)
- **Access Level**: Tenant-specific (read-only)
- **Requires**: Must have `tenant` assigned
- **Capabilities**:
  - View own tenant information only
  - Cannot modify any data
  - View and change own profile/password
  - Cannot manage other users or resources

### 6. Customer
- **Access Level**: Global (entire system)
- **Capabilities**:
  - Same as Super Admin
  - Full access to all resources
  - Can manage everything

---

## Permission Classes

### Core Permission Classes

#### `IsSuperAdmin`
- Only Super Admin users can access
- Used for system-wide operations

#### `IsTenantAdmin`
- Only Tenant Admin users with valid tenant
- Includes object-level checking for tenant ownership

#### `IsCustomer`
- Only Customer users can access

#### `IsTenantUser`
- Tenant Users with read-only access to their tenant

#### `IsInventoryManager`
- Inventory Managers managing their branch
- Object-level permission checks branch ownership

#### `IsCashier`
- Cashier users managing their branch
- Object-level permission checks branch ownership

### Composite Permission Classes

#### `IsSuperAdminOrTenantAdmin`
- Super Admin can do anything globally
- Tenant Admin can only access their tenant's data

#### `IsSuperAdminOrCustomer`
- Both have full system access

#### `CanManageTenantUsers`
- Super Admin can manage all users
- Tenant Admin can manage users in their tenant

#### `CanEditTenantDetails`
- Super Admin can edit all tenant details
- Tenant Admin can edit only their own tenant

#### `CanManageBranchResources`
- Super Admin: manage all resources
- Tenant Admin: manage all branch resources in their tenant
- Inventory Manager: manage inventory in their branch
- Cashier: manage transactions in their branch

#### `IsSuperAdminOrTenantAdminOrBranchManager`
- Hierarchical permissions for all management roles
- Each can manage at their respective level

---

## Permission Utility Functions

### Role Checking Functions

```python
from apps.base.permission_utils import (
    is_super_admin,
    is_tenant_admin,
    is_tenant_user,
    is_customer,
    is_inventory_manager,
    is_cashier
)

# Check user role
if is_super_admin(user):
    # Super admin logic

if is_tenant_admin(user):
    # Tenant admin logic

if is_inventory_manager(user):
    # Inventory manager logic

if is_cashier(user):
    # Cashier logic
```

### Access Checking Functions

```python
from apps.base.permission_utils import (
    can_access_tenant,
    can_manage_tenant,
    can_manage_tenant_users,
    can_manage_user,
    can_manage_branch,
    can_manage_branch_resources
)

# Check tenant access
if can_access_tenant(user, tenant):
    # User can access this tenant

if can_manage_tenant(user, tenant):
    # User can manage this tenant

if can_manage_user(user, target_user):
    # User can manage target user

if can_manage_branch(user, branch):
    # User can manage this branch

if can_manage_branch_resources(user, branch):
    # User can manage resources in this branch
```

### Queryset Filtering Functions

```python
from apps.base.permission_utils import (
    get_tenant_queryset_for_user,
    get_branch_queryset_for_user
)

# Automatically filter querysets by user permissions
filtered_tenants = get_tenant_queryset_for_user(user, Tenant.objects.all())
filtered_inventory = get_branch_queryset_for_user(user, Inventory.objects.all())
```

---

## Implementation in Views

### Example 1: Tenant ViewSet with Super Admin/Tenant Admin

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.base.permissions import IsSuperAdminOrTenantAdmin
from apps.base.permission_utils import get_tenant_queryset_for_user

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
    
    def get_queryset(self):
        # Filter based on user role
        return get_tenant_queryset_for_user(self.request.user, self.queryset)
```

### Example 2: User Management ViewSet

```python
from apps.base.permissions import CanManageTenantUsers
from apps.base.permission_utils import can_manage_user

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, CanManageTenantUsers]
    
    def perform_update(self, serializer):
        if not can_manage_user(self.request.user, serializer.instance):
            raise PermissionDenied()
        super().perform_update(serializer)
```

### Example 3: Inventory Management (Branch-level)

```python
from apps.base.permissions import CanManageBranchResources
from apps.base.permission_utils import get_branch_queryset_for_user

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    permission_classes = [IsAuthenticated, CanManageBranchResources]
    
    def get_queryset(self):
        # Filter by user's branch access
        return get_branch_queryset_for_user(self.request.user, self.queryset)
```

---

## Access Control Rules

### Tenant-Level Access

| User Role | List All | View Other | Create | Update Own | Update Other | Delete |
|-----------|----------|-----------|--------|-----------|--------------|--------|
| Super Admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tenant Admin | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Customer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Others | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### User Management

| User Role | List Tenant | Create User | Update User | Delete User |
|-----------|------------|-------------|-------------|------------|
| Super Admin | ✅ All | ✅ Any | ✅ Any | ✅ Any |
| Tenant Admin | ✅ Own Tenant | ✅ Own Tenant | ✅ Own Tenant | ✅ Own Tenant |
| Inventory Manager | ❌ | ❌ | ❌ Own | ❌ |
| Cashier | ❌ | ❌ | ❌ Own | ❌ |
| Sub Admin | ❌ | ❌ | ❌ Own | ❌ |

### Branch Resource Management

| User Role | List | View | Create | Update | Delete |
|-----------|------|------|--------|--------|--------|
| Super Admin | ✅ All | ✅ All | ✅ Any | ✅ Any | ✅ Any |
| Tenant Admin | ✅ Own Tenant | ✅ Own Tenant | ✅ Own Tenant | ✅ Own Tenant | ✅ Own Tenant |
| Inventory Manager | ✅ Own Branch | ✅ Own Branch | ✅ Own Branch | ✅ Own Branch | ✅ Own Branch |
| Cashier | ✅ Own Branch | ✅ Own Branch | ✅ Own Branch | ✅ Own Branch | ✅ Own Branch |
| Others | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Enforcement Points

### 1. Middleware Level
**File**: `apps/base/middleware.py`
- Sets current tenant/user in thread-local storage
- Used by TenantManager for automatic queryset filtering

### 2. View Level
**Method**: `get_permissions()` in viewsets
- Applied to all requests
- Checks user role and credentials
- Raises PermissionDenied if unauthorized

### 3. Object Level
**Method**: `has_object_permission()` in permission classes
- Checks if user can access specific objects
- Validates tenant/branch ownership
- Prevents cross-tenant access

### 4. Queryset Level
**Method**: `get_queryset()` in viewsets
- Filters data based on user permissions
- Uses utility functions for filtering
- Prevents data leakage between tenants/branches

---

## Testing Permissions

### Quick Tests

```python
from apps.base.permission_utils import is_super_admin, is_tenant_admin

# Test role checking
assert is_super_admin(super_admin_user) == True
assert is_tenant_admin(tenant_admin_user) == True
assert is_tenant_admin(other_tenant_admin) == True  # Different tenant

# Test access
from apps.base.permission_utils import can_manage_tenant
assert can_manage_tenant(super_admin_user, any_tenant) == True
assert can_manage_tenant(tenant_admin_user, own_tenant) == True
assert can_manage_tenant(tenant_admin_user, other_tenant) == False
```

---

## Common Scenarios

### Scenario 1: Tenant Admin Creating User
1. User: Tenant Admin (tenant_id=1)
2. Action: Create user with tenant=1
3. Validation:
   - ✅ Check: User has role ADMIN
   - ✅ Check: User has tenant assigned
   - ✅ Check: Tenant matches user's tenant
   - ✅ Result: User created successfully

### Scenario 2: Tenant Admin Creating User in Different Tenant
1. User: Tenant Admin (tenant_id=1)
2. Action: Create user with tenant=2
3. Validation:
   - ✅ Check: User has role ADMIN
   - ✅ Check: User has tenant assigned
   - ❌ Check: Tenant=2 != user's tenant=1
   - ❌ Result: PermissionDenied

### Scenario 3: Inventory Manager Accessing Inventory
1. User: Inventory Manager (branch_id=5)
2. Action: List inventory
3. Validation:
   - ✅ Check: User has role INVENTORY_MANAGER
   - ✅ Check: User has branch assigned
   - ✅ Filter: Only inventory from branch=5
   - ✅ Result: Inventory from branch 5 returned

### Scenario 4: Cashier Accessing Transactions from Different Branch
1. User: Cashier (branch_id=5)
2. Action: List transactions from branch_id=10
3. Validation:
   - ✅ Check: User has role CASHIER
   - ❌ Check: branch=10 != user's branch=5
   - ❌ Result: Empty queryset returned

---

## Migration Guide

### For Existing Views

1. **Add Permission Classes**:
```python
from apps.base.permissions import IsSuperAdminOrTenantAdmin
permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
```

2. **Update get_queryset()**:
```python
from apps.base.permission_utils import get_tenant_queryset_for_user
def get_queryset(self):
    queryset = super().get_queryset()
    return get_tenant_queryset_for_user(self.request.user, queryset)
```

3. **Add perform_* methods for validation**:
```python
def perform_update(self, serializer):
    self.check_object_permissions(self.request, serializer.instance)
    super().perform_update(serializer)
```

---

## API Responses

### Success Response
```json
{
    "id": 1,
    "username": "user@example.com",
    "role": "admin",
    "tenant": {
        "id": 1,
        "business_name": "My Business"
    }
}
```

### Permission Denied Response
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### Invalid Tenant Response
```json
{
    "detail": "Tenant Admin can only manage users in their own tenant."
}
```

---

## Best Practices

1. **Always Check Permissions**: Use permission classes in all viewsets
2. **Filter Querysets**: Apply `get_tenant_queryset_for_user()` in `get_queryset()`
3. **Validate on Create/Update**: Check tenant/branch in `perform_*` methods
4. **Use Utility Functions**: Prefer utility functions over direct role checks
5. **Test Cross-Tenant Access**: Ensure Tenant Admin cannot access other tenants
6. **Log Access Attempts**: Track who accesses what for auditing

---

## Files Modified

1. `apps/base/permissions.py` - Permission classes
2. `apps/base/permission_utils.py` - Utility functions
3. `apps/users/views/user_view.py` - User management with RBAC
4. `apps/tenant/views/tenant.py` - Tenant management with RBAC
5. `apps/stock_management/views/inventory.py` - Branch-level inventory management
6. `apps/cashandbank/views/cash_transaction.py` - Branch-level transaction management

---

## Support & Questions

For issues or questions about the RBAC system, refer to:
- Permission classes: `apps/base/permissions.py`
- Utility functions: `apps/base/permission_utils.py`
- Implementation examples: View files in respective apps
