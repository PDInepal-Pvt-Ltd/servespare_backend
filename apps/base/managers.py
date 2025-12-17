from django.db import models
from apps.base.tenant import get_current_tenant, get_current_user


class TenantQuerySet(models.QuerySet):
    def _maybe_filter(self):
        tenant = get_current_tenant()
        user = get_current_user()

        # If no tenant is set for the request, do not alter queryset
        if tenant is None:
            return self

        # Superusers can see all data
        if user and getattr(user, 'is_superuser', False):
            return self

        # If model has a `tenant` field, filter by it
        field_names = [f.name for f in self.model._meta.fields]
        if 'tenant' in field_names:
            return self.filter(tenant=tenant)

        return self


class TenantManager(models.Manager):
    """Manager that applies tenant scoping automatically via thread-local tenant.

    Usage: set `objects = TenantManager()` on models that have a `tenant` FK
    so queries are automatically limited to the request's tenant when present.
    """

    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        return qs._maybe_filter()
