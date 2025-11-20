"""
Custom middleware for ToyBox.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.functional import SimpleLazyObject

User = get_user_model()


def get_user_from_token(request):
    """Get user from JWT token in Authorization header."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return AnonymousUser()
    
    token = auth_header.split(' ')[1]
    
    try:
        # Validate token
        validated_token = UntypedToken(token)
        
        # Get user ID from token
        user_id = validated_token.get('user_id')
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                return user
            except User.DoesNotExist:
                return AnonymousUser()
    except (TokenError, InvalidToken, KeyError):
        pass
    
    return AnonymousUser()


class JWTAuthenticationMiddleware:
    """
    Middleware to authenticate users from JWT tokens in Authorization header.
    This allows template views to access request.user when JWT token is present.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only set user if not already authenticated via session
        if not request.user.is_authenticated:
            # Check for JWT token in Authorization header
            user = get_user_from_token(request)
            if user.is_authenticated:
                request.user = user
        
        response = self.get_response(request)
        return response

