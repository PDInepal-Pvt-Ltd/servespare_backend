from typing import Iterable
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

        # Customers should see all tenant data similar to superusers
        try:
            from apps.users.models import User
            if getattr(user, 'role', None) == User.Role.CUSTOMER:
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
        if 'tenant' in field_names:
            return qs.filter(tenant=tenant)

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

        # Customers should see all tenant data similar to superusers
        try:
            from apps.users.models import User
            if getattr(user, 'role', None) == User.Role.CUSTOMER:
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

        # If model has a tenant field, filter by it
        model = getattr(queryset, 'model', None)
        if model is None:
            return queryset

        field_names = [f.name for f in model._meta.fields]
        if 'tenant' in field_names:
            return queryset.filter(tenant=tenant)

        return queryset
