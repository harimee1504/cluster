import os
from functools import wraps
from clerk_backend_api import Clerk
from django.http import JsonResponse
from django.conf import settings
from clerk_backend_api.jwks_helpers.authenticaterequest import AuthenticateRequestOptions
import httpx
from django.core.cache import cache

sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

def get_token_from_request(request):
    """Extract Bearer token from the Authorization header."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return None

class ClerkAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = get_token_from_request(request)
        if not token:
            return self.get_response(request)

        try:
            httpx_request = httpx.Request(
                method=request.method,
                url=request.build_absolute_uri(),
                headers=dict(request.headers),
            )
            auth_state = sdk.authenticate_request(
                httpx_request,
                AuthenticateRequestOptions(
                    audience=["convex", "postmanToken"]
                )
            )
            if auth_state.is_signed_in:
                request.clerk_user = auth_state.payload
                
                # Cache user permissions
                user_id = auth_state.payload["sub"]
                user_permissions = cache.get(f'user_permissions_{user_id}')
                
                if user_permissions is None:
                    user_info = sdk.users.get(user_id=user_id)
                    if "permissions" in user_info.private_metadata:
                        user_permissions = user_info.private_metadata["permissions"]
                    else:
                        user_permissions = []
                    cache.set(f'user_permissions_{user_id}', user_permissions, timeout=3600)  # Cache for 1 hour
                
                request.user_permissions = user_permissions
            
        except Exception as e:
            return JsonResponse({"message": f"Unauthorized - {str(e)}"}, status=401)

        return self.get_response(request)

def login_required(view_func):
    """Decorator to ensure user is authenticated with Clerk."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'clerk_user'):
            return JsonResponse({"message": "Authentication required"}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view

def has_permission(permission):
    """Decorator to check if user has specific permission."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'user_permissions') or permission not in request.user_permissions:
                return JsonResponse({"message": "Permission denied"}, status=403)
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator 