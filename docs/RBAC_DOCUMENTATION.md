# Role-Based Access Control (RBAC) Documentation

## Overview

This system implements a comprehensive Role-Based Access Control (RBAC) system that manages access to resources based on user roles and tenant associations. The system supports four main user roles with distinct permissions and access levels.

## User Roles

### 1. Super Admin
**Role Value:** `super_admin`

**Permissions:**
- ✅ Access all resources globally (across all tenants)
- ✅ Create, read, update, and delete all tenants
- ✅ Create, read, update, and delete users across all tenants
- ✅ Change any user's role or status
- ✅ View all business data across all tenants
- ✅ Manage subscription plans and packages
- ✅ View system-wide analytics and reports

**Use Cases:**
- System administrators
- Platform owners
- Support team members

**Limitations:**
- None

---

### 2. Tenant Admin
**Role Value:** `admin`

**Permissions:**
- ✅ Manage only their own tenant's details
- ✅ Create, read, update users within their tenant
- ✅ Change user roles/status within their tenant
- ✅ View all data within their tenant
- ✅ Manage branch/location settings within their tenant
- ✅ Access inventory, sales, and financial reports for their tenant

**Restrictions:**
- ❌ Cannot access other tenants' data
- ❌ Cannot change their own tenant assignment
- ❌ Cannot move users to different tenants
- ❌ Cannot delete their tenant (only Super Admin)
- ❌ Cannot change subscription plans

**Use Cases:**
- Business owners
- Tenant administrators
- Organization managers

**Example:**
```
User "Alice" (Admin) at Tenant "ABC Corp"
  ✓ Can view all ABC Corp employees
  ✓ Can edit ABC Corp business details
  ✓ Can create new users in ABC Corp
  ✗ Cannot access XYZ Company data
  ✗ Cannot delete ABC Corp
```

---

### 3. Tenant User (Sub Admin)
**Role Value:** `sub_admin`

**Permissions:**
- ✅ View their own tenant's information (read-only)
- ✅ View their own user profile
- ✅ Change own password
- ✅ View admin contact information

**Restrictions:**
- ❌ Cannot create or manage users
- ❌ Cannot change tenant details
- ❌ Cannot access other users' data
- ❌ Cannot change any roles or statuses
- ❌ Cannot edit any tenant settings

**Use Cases:**
- Regular employees
- Staff members
- Department heads

**Example:**
```
User "Bob" (Tenant User) at Tenant "ABC Corp"
  ✓ Can view their own profile
  ✓ Can change their own password
  ✓ Can view ABC Corp business name and contact
  ✗ Cannot create new users
  ✗ Cannot edit any tenant settings
  ✗ Cannot access other employees' profiles
```

---

### 4. Customer
**Role Value:** `customer`

**Permissions:**
- ✅ Access all resources (similar to Super Admin)
- ✅ View all tenants and their data
- ✅ View all users across all tenants
- ✅ Access all business data globally

**Restrictions:**
- ❌ Cannot modify/delete resources (read-only in most contexts)
- ❌ Cannot create or manage users
- ❌ Cannot edit tenant details

**Use Cases:**
- Premium customers with dashboard access
- White-label resellers
- API consumers with read-only access

**Note:** Customer role has read-only access to all resources like Super Admin sees them.

---

## Permission Classes

The system uses Django REST Framework permission classes located in `apps/base/permissions.py`:

### Key Permission Classes

#### `IsSuperAdmin`
- Allows only Super Admin users
- Raises `PermissionDenied` for all other roles

```python
from apps.base.permissions import IsSuperAdmin

class AdminOnlyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
```

#### `IsTenantAdmin`
- Allows only Tenant Admin users with valid tenant assignment
- Object-level permission: Can only access own tenant's data

```python
from apps.base.permissions import IsTenantAdmin

class TenantManagementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTenantAdmin]
```

#### `IsTenantUser`
- Allows only Tenant User (Sub Admin) with valid tenant
- Object-level permission: Read-only access to own tenant data

```python
from apps.base.permissions import IsTenantUser

class TenantUserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsTenantUser]
```

#### `IsCustomer`
- Allows only Customer role users
- Has access similar to Super Admin

```python
from apps.base.permissions import IsCustomer

class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomer]
```

#### `IsSuperAdminOrTenantAdmin`
- Allows Super Admin or Tenant Admin
- Super Admin: Global access
- Tenant Admin: Limited to own tenant

```python
from apps.base.permissions import IsSuperAdminOrTenantAdmin

class TenantViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
```

#### `IsSuperAdminOrCustomer`
- Allows Super Admin or Customer
- Both have full access to resources

```python
from apps.base.permissions import IsSuperAdminOrCustomer

class ResourceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperAdminOrCustomer]
```

#### `CanManageTenantUsers`
- Allows Super Admin (all users) or Tenant Admin (own tenant users)
- Used for user management endpoints

```python
from apps.base.permissions import CanManageTenantUsers

class UserManagementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageTenantUsers]
```

#### `CanEditTenantDetails`
- Allows Super Admin (all tenants) or Tenant Admin (own tenant)
- Used for tenant detail editing endpoints

```python
from apps.base.permissions import CanEditTenantDetails

class TenantDetailViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanEditTenantDetails]
```

---

## Utility Functions

Located in `apps/base/permission_utils.py`, these functions provide helper methods for permission checking:

### Role Checking Functions

```python
from apps.base.permission_utils import (
    is_super_admin,
    is_tenant_admin,
    is_tenant_user,
    is_customer
)

# Check user role
if is_super_admin(user):
    # Allow global access
    
if is_tenant_admin(user):
    # Allow tenant-level access
    
if is_customer(user):
    # Allow broad access
```

### Access Control Functions

```python
from apps.base.permission_utils import (
    can_access_tenant,
    can_manage_tenant,
    can_manage_tenant_users,
    can_manage_user
)

# Check if user can access specific tenant
if can_access_tenant(user, tenant):
    # Grant access
    
# Check if user can manage users in tenant
if can_manage_tenant_users(user, tenant):
    # Allow user creation/editing in tenant
    
# Check if user can manage specific user
if can_manage_user(user, target_user):
    # Allow user update/delete
```

### Queryset Filtering

```python
from apps.base.permission_utils import get_tenant_queryset_for_user

# Automatically filter queryset based on user's role
queryset = get_tenant_queryset_for_user(user, Tenant.objects.all())
# Returns:
# - All tenants for Super Admin/Customer
# - User's tenant only for Tenant Admin/Tenant User
# - Empty queryset for unauthenticated users
```

---

## API Endpoint Permissions

### User Management Endpoints

| Endpoint | Method | Super Admin | Tenant Admin | Tenant User | Customer |
|----------|--------|:----------:|:-----------:|:----------:|:--------:|
| `/api/users/` | GET | ✅ All | ✅ Own tenant | ✅ Own only | ✅ Self only |
| `/api/users/` | POST | ✅ | ✅ Own tenant | ❌ | ❌ |
| `/api/users/{id}/` | GET | ✅ | ✅ Own tenant | ✅ Own | ✅ Own |
| `/api/users/{id}/` | PUT/PATCH | ✅ | ✅ Own tenant | ❌ | ❌ |
| `/api/users/{id}/` | DELETE | ✅ | ✅ Own tenant | ❌ | ❌ |
| `/api/users/me/` | GET | ✅ | ✅ | ✅ | ✅ |
| `/api/users/change_password/` | POST | ✅ | ✅ | ✅ | ✅ |
| `/api/users/reset_password/` | POST | ✅ | ✅ Own tenant | ❌ | ❌ |
| `/api/users/update_role/` | POST | ✅ | ✅ Own tenant | ❌ | ❌ |
| `/api/users/update_status/` | POST | ✅ | ✅ Own tenant | ❌ | ❌ |

### Tenant Management Endpoints

| Endpoint | Method | Super Admin | Tenant Admin | Tenant User | Customer |
|----------|--------|:----------:|:-----------:|:----------:|:--------:|
| `/api/tenants/` | GET | ✅ All | ✅ Own | 🔍 Own (read) | ✅ All |
| `/api/tenants/` | POST | ✅ | ❌ | ❌ | ❌ |
| `/api/tenants/{id}/` | GET | ✅ | ✅ Own | 🔍 Own (read) | ✅ |
| `/api/tenants/{id}/` | PUT/PATCH | ✅ | ✅ Own | ❌ | ❌ |
| `/api/tenants/{id}/` | DELETE | ✅ | ❌ | ❌ | ❌ |
| `/api/tenants/active/` | GET | ✅ All | ✅ If active | 🔍 If active | ✅ All |
| `/api/tenants/by_status/` | GET | ✅ | ✅ | 🔍 | ✅ |

**Legend:**
- ✅ = Full access (read/write)
- 🔍 = Read-only access
- ❌ = No access (returns 403 Forbidden)

---

## Implementation Examples

### Example 1: Creating a Tenant-Filtered ViewSet

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.base.permissions import IsSuperAdminOrTenantAdmin
from apps.base.permission_utils import get_tenant_queryset_for_user

class TenantResourceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
    
    def get_queryset(self):
        # Automatically filters based on user role
        queryset = TenantResource.objects.all()
        return get_tenant_queryset_for_user(self.request.user, queryset)
```

### Example 2: Restricting Creation to Tenant Admin

```python
from apps.base.permission_utils import is_tenant_admin

class UserCreateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CanManageTenantUsers]
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Tenant Admin can only create in their tenant
        if is_tenant_admin(user):
            if serializer.validated_data.get('tenant') != user.tenant:
                raise PermissionDenied("Can only create in your own tenant")
        
        serializer.save(created_by=user)
```

### Example 3: Custom View with Role Check

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.base.permission_utils import check_permission_or_raise, can_manage_tenant

@api_view(['POST'])
def edit_tenant_details(request, tenant_id):
    tenant = Tenant.objects.get(id=tenant_id)
    
    # Will raise PermissionDenied if user can't manage tenant
    check_permission_or_raise(can_manage_tenant, request.user, tenant)
    
    # Process the request
    return Response({'status': 'updated'})
```

---

## Migration Guide

### For Existing Projects

If you have an existing project with different permission logic, follow these steps:

1. **Update User Models:**
   - Ensure all users have a `role` field with one of the four roles
   - Ensure `tenant` is properly assigned for non-super-admin users

2. **Update Views:**
   - Import permission classes from `apps.base.permissions`
   - Add `permission_classes` to your ViewSets
   - Override `get_queryset()` to filter based on user role

3. **Update Serializers:**
   - Add validation in `validate()` methods to respect permissions
   - Use read-only fields for users who shouldn't modify them

4. **Test Permissions:**
   - Test each endpoint with each role
   - Verify forbidden access returns 403
   - Verify allowed access returns correct data

---

## Security Best Practices

1. **Always Check Object Permissions:**
   ```python
   self.check_object_permissions(self.request, obj)
   ```

2. **Validate Tenant Assignment:**
   - Prevent users from assigning themselves to different tenants
   - Only Super Admin can create users across tenants

3. **Audit Sensitive Operations:**
   - Log user management changes
   - Log tenant setting changes
   - Track who changed what and when

4. **Use Read-Only Fields:**
   - Don't allow users to change `tenant` or `role` unless authorized
   - Use `read_only_fields` in serializers

5. **Validate Input:**
   - Check that users can only manage resources they have access to
   - Prevent privilege escalation attempts

---

## Troubleshooting

### User Getting "Permission Denied" Unexpectedly

**Cause:** User's role doesn't match endpoint permission requirement

**Solution:**
1. Check user's role: `user.role`
2. Check user's tenant: `user.tenant`
3. Verify permission classes on endpoint
4. Review get_queryset() filtering logic

### Tenant Admin Can See Other Tenants' Data

**Cause:** Missing tenant filtering in get_queryset()

**Solution:**
```python
def get_queryset(self):
    queryset = Model.objects.all()
    return get_tenant_queryset_for_user(self.request.user, queryset)
```

### Customer Role Not Working as Expected

**Cause:** Customer role might need different permission class

**Solution:**
- If customers should have read-only access: Use `IsCustomer`
- If customers should have full access: Use `IsSuperAdminOrCustomer`
- Add custom permission class if needed

---

## Future Enhancements

1. **Fine-Grained Permissions:**
   - Implement module-level permissions (e.g., "can access inventory")
   - Add action-level permissions (e.g., "can view sales reports")

2. **Custom Roles:**
   - Allow creating custom roles with specific permissions
   - Role templates for common scenarios

3. **Permission Caching:**
   - Cache permission checks for performance
   - Invalidate cache on role/tenant changes

4. **Audit Trail:**
   - Log all access to sensitive data
   - Generate access reports

5. **Multi-Tenant Features:**
   - Allow users to access multiple tenants (with appropriate roles)
   - Switch between tenant contexts
