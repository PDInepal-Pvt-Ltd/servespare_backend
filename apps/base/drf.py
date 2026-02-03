from typing import Iterable
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class TenantViewSetMixin:
    """Mixin for DRF viewsets to scope their querysets to the request user's tenant.

    Add this as the first base class for viewsets that should be tenant-scoped:
        class MyView(TenantViewSetMixin, viewsets.ModelViewSet):
            ...
    """

    def filter_queryset(self, queryset):
        """Filter an existing queryset to the current user's tenant.

        Call the parent `filter_queryset` first so DRF's configured
        filter backends (search, ordering, filtering) are applied, then
        enforce tenant scoping on the resulting queryset.
        """
        # Let DRF apply other filter backends first
        try:
            qs = super().filter_queryset(queryset)
        except Exception:
            qs = queryset

        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None)

        if user is None or not getattr(user, 'is_authenticated', False):
            return qs

        # Super Admin and Customers should see all tenant data
        try:
            from apps.users.models import User
            user_role = getattr(user, 'role', None)
            if user_role in [User.Role.CUSTOMER, User.Role.SUPER_ADMIN]:
                return qs
        except Exception:
            pass

        if getattr(user, 'is_superuser', False):
            return qs

        tenant = getattr(user, 'tenant', None)
        if tenant is None:
            try:
                return qs.none()
            except Exception:
                return qs

        model = getattr(qs, 'model', None)
        if model is None:
            return qs

        field_names = [f.name for f in model._meta.fields]
        m2m_names = {f.name for f in getattr(model._meta, 'many_to_many', [])}

        has_tenants_m2m = 'tenants' in m2m_names
        if 'tenant' in field_names:
            # Support models that can involve multiple tenants via M2M `tenants`
            if has_tenants_m2m:
                return qs.filter(Q(tenant=tenant) | Q(tenants=tenant)).distinct()
            return qs.filter(tenant=tenant)
        if has_tenants_m2m:
            return qs.filter(tenants=tenant).distinct()

        # Some models (e.g. Parties) don't have a direct `tenant` field but
        # are associated to a tenant via the `created_by` user. In that case
        # allow scoping by `created_by__tenant` so records created by users
        # in the same tenant are visible to other users of that tenant.
        if 'created_by' in field_names:
            try:
                return qs.filter(created_by__tenant=tenant)
            except Exception:
                # If filtering by related field fails for some reason,
                # fall back to returning the original queryset (safer).
                return qs

        return qs


class TenantFilterBackend(BaseFilterBackend):
    """DRF filter backend that restricts querysets to the request user's tenant.

    Add this to `DEFAULT_FILTER_BACKENDS` in REST_FRAMEWORK to apply globally.
    """

    def filter_queryset(self, request, queryset, view):
        user = getattr(request, 'user', None)

        # If no authenticated user or superuser, don't filter
        if user is None or not getattr(user, 'is_authenticated', False):
            return queryset

        # Super Admin and Customers should see all tenant data
        try:
            from apps.users.models import User
            user_role = getattr(user, 'role', None)
            if user_role in [User.Role.CUSTOMER, User.Role.SUPER_ADMIN]:
                return queryset
        except Exception:
            pass

        if getattr(user, 'is_superuser', False):
            return queryset

        tenant = getattr(user, 'tenant', None)
        if tenant is None:
            # No tenant on user -> don't expose tenant-scoped records
            try:
                # If queryset supports .none()
                return queryset.none()
            except Exception:
                return queryset

        # If model has a tenant field, filter by it (or by M2M `tenants` if present)
        model = getattr(queryset, 'model', None)
        if model is None:
            return queryset

        field_names = [f.name for f in model._meta.fields]
        m2m_names = {f.name for f in getattr(model._meta, 'many_to_many', [])}

        has_tenants_m2m = 'tenants' in m2m_names
        if 'tenant' in field_names:
            if has_tenants_m2m:
                return queryset.filter(Q(tenant=tenant) | Q(tenants=tenant)).distinct()
            return queryset.filter(tenant=tenant)
        if has_tenants_m2m:
            return queryset.filter(tenants=tenant).distinct()

        # Support models without direct `tenant` field but with `created_by`
        # referencing a User whose `tenant` should be used for scoping.
        if 'created_by' in field_names:
            try:
                return queryset.filter(created_by__tenant=tenant)
            except Exception:
                return queryset

        return queryset
