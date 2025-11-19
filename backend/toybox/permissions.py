"""
Custom permissions for ToyBox API.
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()


class RoleGuard(permissions.BasePermission):
    """Permission class based on user role."""
    
    allowed_roles = []
    
    def has_permission(self, request, view):
        """Check if user has required role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        user_role = request.user.role
        return user_role in self.allowed_roles


class IsAdmin(RoleGuard):
    """Only ADMIN role allowed."""
    allowed_roles = [User.Role.ADMIN]


class IsAdminOrSuperuser(RoleGuard):
    """ADMIN or SUPERUSER role allowed."""
    allowed_roles = [User.Role.ADMIN, User.Role.SUPERUSER]


class IsAdminOrAyatori(RoleGuard):
    """ADMIN or SUPERUSER role allowed (legacy name for compatibility)."""
    allowed_roles = [User.Role.ADMIN, User.Role.SUPERUSER]


class IsAdminOrOffice(RoleGuard):
    """ADMIN or SUPERUSER role allowed (legacy name for compatibility)."""
    allowed_roles = [User.Role.ADMIN, User.Role.SUPERUSER]


class IsAdminOrAyatoriOrOffice(RoleGuard):
    """ADMIN or SUPERUSER role allowed (legacy name for compatibility)."""
    allowed_roles = [User.Role.ADMIN, User.Role.SUPERUSER]


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to only allow owners to edit."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is owner of the object."""
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if object has author/user field
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False

