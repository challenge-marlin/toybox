"""
Custom context processors for Django templates.
"""
from django.conf import settings


def admin_url(request):
    """Add ADMIN_URL to template context."""
    return {
        'ADMIN_URL': getattr(settings, 'ADMIN_URL', 'admin'),
    }


