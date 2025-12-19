# Role-Based Access Control Implementation Guide

## Quick Start

This guide explains how to implement role-based access control (RBAC) in your views and serializers.

## Files Created/Modified

### New Files
1. **`apps/base/permissions.py`** - Permission classes for DRF
2. **`apps/base/permission_utils.py`** - Utility functions for permission checks
3. **`docs/RBAC_DOCUMENTATION.md`** - Comprehensive documentation

### Modified Files
1. **`apps/tenant/views/tenant.py`** - Added permission classes to TenantViewSet
2. **`apps/users/views/user_view.py`** - Added permission classes and role-based filtering

## Role Summary

| Role | Access | Can Manage |
|------|--------|-----------|
| **Super Admin** | Everything globally | Everything |
| **Tenant Admin** | Own tenant only | Own tenant users & details |
| **Tenant User** | Own tenant (read-only) | Own password only |
| **Customer** | Everything (like Super Admin) | Limited based on context |

## Using in Your Views

### 1. Add Permission Classes to ViewSet

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.base.permissions import IsSuperAdminOrTenantAdmin

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
    
    def get_queryset(self):
        from apps.base.permission_utils import get_tenant_queryset_for_user
        queryset = MyModel.objects.all()
        return get_tenant_queryset_for_user(self.request.user, queryset)
```

### 2. Add Validation in perform_create/perform_update

```python
from apps.base.permission_utils import can_manage_user, is_tenant_admin

def perform_create(self, serializer):
    user = self.request.user
    
    # Validate tenant assignment
    if is_tenant_admin(user):
        if serializer.validated_data.get('tenant') != user.tenant:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Can only create in your own tenant")
    
    serializer.save(created_by=user)

def perform_update(self, serializer):
    user = self.request.user
    target = serializer.instance
    
    # Validate user can manage target
    if not can_manage_user(user, target):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You don't have permission to update this")
    
    serializer.save()
```

### 3. Use Role Checks in Methods

```python
from apps.base.permission_utils import is_super_admin, is_tenant_admin

def get_report_data(self, request):
    if is_super_admin(request.user):
        # Return global data
        return GlobalReport.objects.all()
    elif is_tenant_admin(request.user):
        # Return tenant-specific data
        return GlobalReport.objects.filter(tenant=request.user.tenant)
    else:
        # Return user-specific data
        return GlobalReport.objects.filter(user=request.user)
```

## Permission Classes Overview

### For Super Admin Only
```python
from apps.base.permissions import IsSuperAdmin
permission_classes = [IsAuthenticated, IsSuperAdmin]
```

### For Super Admin or Tenant Admin
```python
from apps.base.permissions import IsSuperAdminOrTenantAdmin
permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
```

### For Managing Tenant Users
```python
from apps.base.permissions import CanManageTenantUsers
permission_classes = [IsAuthenticated, CanManageTenantUsers]
```

### For Managing Tenant Details
```python
from apps.base.permissions import CanEditTenantDetails
permission_classes = [IsAuthenticated, CanEditTenantDetails]
```

### For Tenant Users Only (Read-Only)
```python
from apps.base.permissions import IsTenantUser
permission_classes = [IsAuthenticated, IsTenantUser]
```

## Utility Functions Reference

### Role Checking

```python
from apps.base.permission_utils import (
    is_super_admin,        # Returns True if user is Super Admin
    is_tenant_admin,       # Returns True if user is Tenant Admin
    is_tenant_user,        # Returns True if user is Tenant User
    is_customer            # Returns True if user is Customer
)
```

### Access Checking

```python
from apps.base.permission_utils import (
    can_access_tenant,      # Check if user can access a tenant
    can_manage_tenant,      # Check if user can manage a tenant
    can_manage_tenant_users, # Check if user can manage users in tenant
    can_manage_user         # Check if user can manage a specific user
)
```

### Queryset Filtering

```python
from apps.base.permission_utils import get_tenant_queryset_for_user

# Automatically filters queryset based on user role
filtered_qs = get_tenant_queryset_for_user(user, queryset)
```

## Common Patterns

### Pattern 1: Admin-Only Endpoint

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.base.permissions import CanManageTenantUsers

class UserViewSet(viewsets.ModelViewSet):
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanManageTenantUsers]
    )
    def create_bulk_users(self, request):
        # Code here is protected by CanManageTenantUsers permission
        return Response({'status': 'created'})
```

### Pattern 2: Tenant-Filtered ViewSet

```python
from apps.base.permission_utils import get_tenant_queryset_for_user

class ProductViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = Product.objects.all()
        # Automatically filters by tenant for non-super-admin users
        return get_tenant_queryset_for_user(self.request.user, queryset)
```

### Pattern 3: Role-Based Response

```python
from apps.base.permission_utils import is_super_admin

class ReportViewSet(viewsets.ViewSet):
    def list(self, request):
        if is_super_admin(request.user):
            data = self.get_global_report()
        elif is_tenant_admin(request.user):
            data = self.get_tenant_report(request.user.tenant)
        else:
            data = self.get_user_report(request.user)
        
        return Response(data)
```

### Pattern 4: Validate Tenant Assignment

```python
from apps.base.permission_utils import is_tenant_admin

def perform_create(self, serializer):
    user = self.request.user
    
    if is_tenant_admin(user):
        # Force tenant to be user's tenant
        serializer.validated_data['tenant'] = user.tenant
    
    serializer.save(created_by=user)
```

## Testing Permissions

### Test Super Admin Access

```python
from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User

class PermissionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='super_admin'
        )
    
    def test_super_admin_can_access_all_tenants(self):
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get('/api/tenants/')
        self.assertEqual(response.status_code, 200)
```

### Test Tenant Admin Restriction

```python
def test_tenant_admin_limited_access(self):
    tenant1 = Tenant.objects.create(business_name="Tenant 1")
    tenant2 = Tenant.objects.create(business_name="Tenant 2")
    
    admin = User.objects.create_user(
        username='admin1',
        password='pass123',
        role='admin',
        tenant=tenant1
    )
    
    self.client.force_authenticate(user=admin)
    response = self.client.get('/api/tenants/')
    
    # Admin should only see their tenant
    self.assertEqual(len(response.data), 1)
    self.assertEqual(response.data[0]['id'], tenant1.id)
```

## API Response Examples

### Success (Super Admin Can Access All)

```
GET /api/tenants/
Authorization: Bearer <token>

Response 200:
{
    "count": 2,
    "results": [
        {"id": 1, "business_name": "ABC Corp", ...},
        {"id": 2, "business_name": "XYZ Company", ...}
    ]
}
```

### Restricted (Tenant Admin Can Access Only Own)

```
GET /api/tenants/
Authorization: Bearer <tenant_admin_token>

Response 200:
{
    "count": 1,
    "results": [
        {"id": 1, "business_name": "ABC Corp", ...}
    ]
}
```

### Permission Denied

```
POST /api/tenants/1/
Authorization: Bearer <tenant_admin_token>
Body: {"business_name": "Other Company"}

Response 403:
{
    "detail": "You do not have permission to perform this action."
}
```

## Migrating Existing Code

### Step 1: Identify Views That Need Permissions

Find all ViewSets and API views that handle sensitive data.

### Step 2: Add Permission Classes

```python
# Before
class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()

# After
from rest_framework.permissions import IsAuthenticated
from apps.base.permissions import IsSuperAdminOrTenantAdmin

class MyViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
```

### Step 3: Add Queryset Filtering

```python
# Before
def get_queryset(self):
    return MyModel.objects.all()

# After
from apps.base.permission_utils import get_tenant_queryset_for_user

def get_queryset(self):
    queryset = MyModel.objects.all()
    return get_tenant_queryset_for_user(self.request.user, queryset)
```

### Step 4: Add Validation in perform_* Methods

```python
# Add permission checks before saving
def perform_update(self, serializer):
    from apps.base.permission_utils import can_manage_user
    
    if not can_manage_user(self.request.user, serializer.instance):
        raise PermissionDenied("You don't have permission")
    
    serializer.save()
```

### Step 5: Test All Endpoints

- Test with Super Admin (should work)
- Test with Tenant Admin (should work for own tenant only)
- Test with Tenant User (should be limited)
- Test with unauthorized user (should get 403)

## Debugging

### Check User Role and Tenant

```python
print(f"Role: {user.role}")
print(f"Tenant: {user.tenant}")
print(f"Is Super Admin: {is_super_admin(user)}")
print(f"Is Tenant Admin: {is_tenant_admin(user)}")
```

### Check Permission Result

```python
from apps.base.permission_utils import can_access_tenant

result = can_access_tenant(user, tenant)
print(f"Can access tenant: {result}")
```

### View Queryset Output

```python
def get_queryset(self):
    qs = MyModel.objects.all()
    filtered_qs = get_tenant_queryset_for_user(self.request.user, qs)
    print(f"Original count: {qs.count()}")
    print(f"Filtered count: {filtered_qs.count()}")
    return filtered_qs
```

## Next Steps

1. Review [RBAC_DOCUMENTATION.md](RBAC_DOCUMENTATION.md) for detailed information
2. Apply permission classes to remaining views
3. Add validation to serializers
4. Create comprehensive tests
5. Update frontend to handle 403 responses
