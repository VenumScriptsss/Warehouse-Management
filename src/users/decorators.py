from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")

            if request.user.role not in allowed_roles:
                raise PermissionDenied(f"Role {request.user.role} not allowed")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def permission_required(permission_codename):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(permission_codename):
                raise PermissionDenied(f"Permission {permission_codename} required")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator