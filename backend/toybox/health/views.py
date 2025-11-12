"""
Health check views.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """Basic health check endpoint."""
    return JsonResponse({'status': 'ok'})


def readiness_check(request):
    """Readiness check - verifies database connectivity."""
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache (Redis)
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        
        return JsonResponse({'ready': True})
    except Exception as e:
        return JsonResponse({'ready': False, 'error': str(e)}, status=503)

