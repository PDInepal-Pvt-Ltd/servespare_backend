from typing import Iterable


class TenantAdminMixin:
    """Admin mixin that scopes queryset to `request.user.tenant` for non-superusers.

    Add this mixin as the first base class for ModelAdmin/UserAdmin classes:
        class MyAdmin(TenantAdminMixin, admin.ModelAdmin):
            ...
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # superusers can see everything
        if request.user and getattr(request.user, 'is_superuser', False):
            return qs

        tenant = getattr(request.user, 'tenant', None)
        if tenant is None:
            # If the requesting user has no tenant, don't expose tenant-scoped records
            return qs.none()

        # If model has a tenant field, filter by it
        field_names = [f.name for f in getattr(self.model, '_meta').fields]
        if 'tenant' in field_names:
            return qs.filter(tenant=tenant)

        return qs
from django.contrib import admin

# Register your models here.
