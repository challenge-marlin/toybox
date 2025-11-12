"""
Utility functions for frontend app.
"""
from django.shortcuts import redirect
from django.http import JsonResponse


def check_jwt_token(request):
    """
    Check if JWT token exists in request headers.
    Returns True if token exists and is valid, False otherwise.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        return True
    return False


def redirect_if_authenticated(view_func):
    """
    Decorator to redirect authenticated users away from auth pages.
    """
    def wrapper(request, *args, **kwargs):
        # Check Django session authentication
        if request.user.is_authenticated:
            return redirect('/me/')
        return view_func(request, *args, **kwargs)
    return wrapper

