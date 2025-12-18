import threading

_state = threading.local()


def set_current_tenant(tenant) -> None:
    """Store the current tenant in thread-local storage."""
    setattr(_state, 'tenant', tenant)


def get_current_tenant():
    """Return the tenant stored for current thread, or None."""
    return getattr(_state, 'tenant', None)


def set_current_user(user) -> None:
    """Store current request user in thread-local storage."""
    setattr(_state, 'user', user)


def get_current_user():
    """Return the current request user for this thread, or None."""
    return getattr(_state, 'user', None)


def clear_current() -> None:
    """Clear stored tenant and user for the current thread."""
    for attr in ('tenant', 'user'):
        if hasattr(_state, attr):
            delattr(_state, attr)
