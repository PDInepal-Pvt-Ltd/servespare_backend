from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from apps.base.tenant import get_current_tenant, get_current_user


class TenantQuerySet(models.QuerySet):
    def _maybe_filter(self):
        tenant = get_current_tenant()
        user = get_current_user()

        # Exclude soft-deleted records if the model has an is_removed field
        field_names = [f.name for f in self.model._meta.fields]
        qs = self
        if 'is_removed' in field_names:
            qs = qs.filter(is_removed=False)

        # If no tenant is set for the request, do not alter queryset further
        if tenant is None:
            return qs

        # Superusers can see all data (except soft-deleted)
        if user and getattr(user, 'is_superuser', False):
            return qs

        # Only apply filters when fields exist on the model. Some models use
        # `deleted_at` or `is_removed` instead of a soft-delete field; only
        # filter when present to avoid FieldError during imports (e.g. ModelForm
        # field generation).
        field_names = [f.name for f in self.model._meta.fields]

        qs = self
        if 'deleted_at' in field_names:
            qs = qs.filter(deleted_at__isnull=True)
        elif 'is_removed' in field_names:
            qs = qs.filter(is_removed=False)

        # If model has a `tenant` field, filter by it
        if 'tenant' in field_names:
            qs = qs.filter(tenant=tenant)

        return qs


class TenantManager(DjangoUserManager):
    """Manager that applies tenant scoping automatically via thread-local tenant.

    Usage: set `objects = TenantManager()` on models that have a `tenant` FK
    so queries are automatically limited to the request's tenant when present.
    """

    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        return qs._maybe_filter()

    # Ensure compatibility with Django auth which calls
    # `<User>._default_manager.get_by_natural_key(username)` during authentication
    def get_by_natural_key(self, username):
        # Resolve the model's username field dynamically (defaults to 'username' for User)
        username_field = getattr(self.model, 'USERNAME_FIELD', 'username')
        return self.get(**{username_field: username})

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Force CLI-created superusers to use the Super Admin role."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # Always pin the role to Super Admin so `createsuperuser` users get full access
        if hasattr(self.model, 'Role') and hasattr(self.model.Role, 'SUPER_ADMIN'):
            extra_fields['role'] = self.model.Role.SUPER_ADMIN
        else:
            extra_fields['role'] = 'super_admin'

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return super().create_superuser(username, email=email, password=password, **extra_fields)
