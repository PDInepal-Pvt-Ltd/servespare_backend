from django.utils.deprecation import MiddlewareMixin
from apps.base.tenant import set_current_tenant, set_current_user, clear_current


class TenantMiddleware(MiddlewareMixin):
    """Stores current request user and tenant in thread-local storage.

    - If `request.user` has a `tenant` attribute, it will be used.
    - Superusers are allowed to access all tenants (no filtering).

    Models that should be tenant-scoped can use `apps.base.managers.TenantManager`.
    """

    def process_request(self, request):
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            set_current_user(user)
            tenant = getattr(user, 'tenant', None)
            set_current_tenant(tenant)
        else:
            set_current_user(None)
            set_current_tenant(None)

    def process_response(self, request, response):
        clear_current()
        return response

    def process_exception(self, request, exception):
        clear_current()
