from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.db import connection
from apps.base.tenant import set_current_tenant, set_current_user, clear_current


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For may contain multiple IPs; first is client
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


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
        # Don't log here; AuditMiddleware will handle logging


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware that records write operations and auth events in `AuditLog`.

    - Logs non-safe HTTP methods (POST, PUT, PATCH, DELETE)
    - Also logs requests under `/api/token` and `/api/auth` as auth events
    - Stores request user, tenant, path, method, status, basic payload snapshot
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def _should_log(self, request):
        method = request.method.upper()
        if method not in self.SAFE_METHODS:
            return True
        path = request.path.lower()
        if path.startswith('/api/token') or '/auth' in path:
            return True
        return False

    def _infer_action(self, method: str, path: str) -> str:
        method = method.upper()
        if method == 'POST':
            return 'create'
        if method in ('PUT', 'PATCH'):
            return 'update'
        if method == 'DELETE':
            return 'delete'
        if 'token' in path or 'auth' in path:
            return 'auth'
        return 'other'

    def process_response(self, request, response):
        try:
            if not self._should_log(request):
                return response

            # Lazy import to avoid circulars at startup
            from apps.base.models import AuditLog

            user = getattr(request, 'user', None)
            tenant = getattr(user, 'tenant', None) if user and getattr(user, 'is_authenticated', False) else None

            # Collect a small, safe snapshot of request data
            payload = None
            try:
                if request.method.upper() in {'POST', 'PUT', 'PATCH', 'DELETE'}:
                    # Prefer parsed data; fallback avoids consuming body
                    data = getattr(request, 'data', None)
                    if data:
                        # Limit size to keep row small
                        from django.forms.models import model_to_dict  # noqa
                        # Coerce to plain types where possible
                        payload = {}
                        for k, v in data.items():
                            try:
                                # Convert non-serializable to string
                                payload[k] = v if isinstance(v, (str, int, float, bool, type(None), list, dict)) else str(v)
                            except Exception:
                                payload[k] = str(v)
                        # Trim overly large payloads
                        try:
                            import json
                            s = json.dumps(payload)
                            if len(s) > 4000:
                                payload = {"_truncated": True}
                        except Exception:
                            payload = None
            except Exception:
                payload = None

            # Resolve client metadata
            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:512]

            action = self._infer_action(request.method, request.path)

            # Optionally infer entity from path: e.g., /api/sales/orders/ -> sales.orders
            entity = None
            try:
                path = request.path.strip('/').split('/')
                if len(path) >= 2 and path[0] == 'api':
                    entity = '.'.join(path[1:3]) if len(path) >= 3 else path[1]
            except Exception:
                entity = None

            AuditLog.objects.create(
                user=user if getattr(user, 'is_authenticated', False) else None,
                tenant=tenant,
                method=request.method.upper(),
                path=request.path[:512],
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=getattr(response, 'status_code', None),
                action=action,
                entity=entity,
                payload=payload,
            )
        except Exception:
            # Never break the request flow due to audit logging
            pass
        return response
