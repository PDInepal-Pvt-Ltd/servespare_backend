# RBAC Quick Reference Card

## Role Permission Matrix (Quick View)

```
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│ Action       │ S.Admin  │ T.Admin  │ T.User   │ Customer │
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ View Tenant  │ ALL      │ OWN      │ OWN(RO)  │ ALL      │
│ Edit Tenant  │ ALL      │ OWN      │ ❌       │ ❌       │
│ Create User  │ ANY      │ OWN TEN  │ ❌       │ ❌       │
│ Edit User    │ ALL      │ OWN TEN  │ ❌       │ ❌       │
│ View Users   │ ALL      │ OWN TEN  │ SELF     │ ALL      │
│ Change Pass  │ ALL      │ ALL      │ SELF     │ SELF     │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
RO = Read-Only, OWN = Own Only, TEN = Tenant
S.Admin = Super Admin, T.Admin = Tenant Admin, T.User = Tenant User
```

## Permission Classes Quick Lookup

| Need | Import | Usage |
|------|--------|-------|
| Super Admin only | `IsSuperAdmin` | `permission_classes = [IsAuthenticated, IsSuperAdmin]` |
| Super or Tenant Admin | `IsSuperAdminOrTenantAdmin` | `[IsAuthenticated, IsSuperAdminOrTenantAdmin]` |
| Manage users | `CanManageTenantUsers` | `[IsAuthenticated, CanManageTenantUsers]` |
| Edit tenant | `CanEditTenantDetails` | `[IsAuthenticated, CanEditTenantDetails]` |
| Customer | `IsCustomer` | `[IsAuthenticated, IsCustomer]` |
| Tenant User | `IsTenantUser` | `[IsAuthenticated, IsTenantUser]` |

## Utility Functions Quick Lookup

```python
# Role checks
from apps.base.permission_utils import is_super_admin, is_tenant_admin, is_customer
if is_super_admin(user): ...

# Access checks
from apps.base.permission_utils import can_manage_user, can_manage_tenant
if can_manage_user(user, target_user): ...

# Queryset filtering
from apps.base.permission_utils import get_tenant_queryset_for_user
qs = get_tenant_queryset_for_user(user, queryset)
```

## Common Code Snippets

### Protect ViewSet with Permissions
```python
from apps.base.permissions import IsSuperAdminOrTenantAdmin

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
```

### Filter by User's Tenant
```python
from apps.base.permission_utils import get_tenant_queryset_for_user

def get_queryset(self):
    qs = Model.objects.all()
    return get_tenant_queryset_for_user(self.request.user, qs)
```

### Validate Tenant Assignment
```python
from apps.base.permission_utils import is_tenant_admin

def perform_create(self, serializer):
    user = self.request.user
    if is_tenant_admin(user):
        if serializer.validated_data.get('tenant') != user.tenant:
            raise PermissionDenied("Can only create in own tenant")
    serializer.save(created_by=user)
```

### Check Permission Before Action
```python
from apps.base.permission_utils import can_manage_user

def perform_update(self, serializer):
    if not can_manage_user(self.request.user, serializer.instance):
        raise PermissionDenied("No permission")
    serializer.save()
```

## API Endpoints - Permissions Applied

| Endpoint | Method | Permissions |
|----------|--------|------------|
| `/api/tenants/` | GET | IsAuthenticated + IsSuperAdminOrTenantAdmin |
| `/api/tenants/` | POST | IsAuthenticated + IsSuperAdminOrTenantAdmin |
| `/api/tenants/{id}/` | PUT/PATCH | IsAuthenticated + IsSuperAdminOrTenantAdmin |
| `/api/users/` | GET | IsAuthenticated (filtered by role) |
| `/api/users/` | POST | IsAuthenticated + CanManageTenantUsers |
| `/api/users/{id}/` | GET | IsAuthenticated (own/tenant/all) |
| `/api/users/{id}/` | PUT/PATCH | IsAuthenticated + CanManageTenantUsers |
| `/api/users/me/` | GET | IsAuthenticated |
| `/api/users/change_password/` | POST | IsAuthenticated |

## Testing Permissions

```bash
# Test with Super Admin
curl -H "Authorization: Bearer $SUPER_ADMIN_TOKEN" http://localhost:8000/api/tenants/

# Test with Tenant Admin (should see only own tenant)
curl -H "Authorization: Bearer $TENANT_ADMIN_TOKEN" http://localhost:8000/api/tenants/

# Test with Tenant User (should get 403)
curl -H "Authorization: Bearer $TENANT_USER_TOKEN" http://localhost:8000/api/tenants/

# Test create as Tenant Admin (should fail if wrong tenant)
curl -X POST -H "Authorization: Bearer $TENANT_ADMIN_TOKEN" \
     -d '{"tenant": "other_tenant_id"}' \
     http://localhost:8000/api/users/
```

## Error Responses

| Scenario | Status | Response |
|----------|--------|----------|
| Not authenticated | 401 | `{"detail": "Authentication credentials not provided"}` |
| No permission | 403 | `{"detail": "You do not have permission to perform this action"}` |
| Access denied | 403 | `{"detail": "Tenant Admin can only create users in their own tenant"}` |
| Invalid data | 400 | `{"field": ["error message"]}` |

## Files Reference

| File | Purpose |
|------|---------|
| `apps/base/permissions.py` | Permission classes for DRF |
| `apps/base/permission_utils.py` | Helper functions |
| `apps/tenant/views/tenant.py` | Tenant endpoints (updated) |
| `apps/users/views/user_view.py` | User endpoints (updated) |
| `docs/RBAC_DOCUMENTATION.md` | Full documentation |
| `docs/RBAC_IMPLEMENTATION_GUIDE.md` | Implementation guide |

## Debugging Tips

```python
# Check user's role and tenant
print(f"Role: {user.role}")
print(f"Tenant: {user.tenant}")

# Check permission result
from apps.base.permission_utils import can_manage_user
print(f"Can manage: {can_manage_user(user, target)}")

# Check queryset filtering
from apps.base.permission_utils import get_tenant_queryset_for_user
qs = get_tenant_queryset_for_user(user, MyModel.objects.all())
print(f"Filtered count: {qs.count()}")
```

## Checklists

### When Adding a New View

- [ ] Add permission classes
- [ ] Override get_queryset() with filtering
- [ ] Add validation in perform_create()
- [ ] Add validation in perform_update()
- [ ] Add validation in perform_destroy()
- [ ] Test with each role
- [ ] Test cross-tenant access (should fail)

### When Modifying an Existing View

- [ ] Check if it has permission classes
- [ ] Check if queryset is filtered by role
- [ ] Check if perform_* methods validate permissions
- [ ] Add missing checks if needed
- [ ] Test after changes

### Before Deploying

- [ ] All views have permission classes
- [ ] All querysets are filtered by role
- [ ] All perform_* methods validate
- [ ] No test failures
- [ ] No permission warnings
- [ ] Documentation updated

## Quick Decision Tree

**What permission class should I use?**

```
┌─────────────────────────────────────────────────────┐
│ Does Super Admin need access?                       │
├─ YES ─┬─────────────────────────────────────────┐   │
│       │ Does Tenant Admin need access?          │   │
│       ├─ YES ─┬──────────────────────────────┐  │   │
│       │       │ IsSuperAdminOrTenantAdmin    │  │   │
│       │       └──────────────────────────────┘  │   │
│       │                                         │   │
│       └─ NO ───┬─────────────────────────────┐ │   │
│               │ IsSuperAdmin                 │ │   │
│               └─────────────────────────────┘ │   │
│                                               │   │
└─ NO ──────────────────────────────────────────┘   │
        Does Tenant Admin need access?              │
        ├─ YES ──── IsTenantAdmin                   │
        └─ NO ────── IsAuthenticated                │
```

## Role Cheat Sheet

### Super Admin
- ✅ Can do anything
- ❌ No restrictions
- Default for system setup

### Tenant Admin
- ✅ Manage own tenant
- ✅ Manage own tenant's users
- ❌ Cannot access other tenants
- Default for business owners

### Tenant User
- ✅ View own tenant (read-only)
- ✅ Change own password
- ❌ Cannot create/edit users
- Default for employees

### Customer
- ✅ Like Super Admin for most cases
- Context-dependent restrictions
- For premium clients

---

**Last Updated:** December 18, 2025
