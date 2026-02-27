from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from functools import wraps

def role_required(allowed_roles=[]):
    """
    Decorator for views that checks whether a user has a particular role.
    Handles both standard and AJAX requests.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Check if user is logged in and has the required role
            if request.user.is_authenticated and request.user.profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # 2. If it's an AJAX request, return JSON instead of a redirect/403 page
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'Access restricted to {", ".join(allowed_roles)}.'
                }, status=403)
            
            # 3. For standard requests, raise PermissionDenied (shows 403.html)
            raise PermissionDenied
        return _wrapped_view
    return decorator