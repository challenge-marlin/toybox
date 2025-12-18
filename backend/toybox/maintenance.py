"""
Maintenance mode middleware.

When enabled, normal pages show a maintenance screen based on the TOP page assets.
Admin and health endpoints remain accessible.
"""

from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render


class MaintenanceModeMiddleware:
    """
    If SiteMaintenance.enabled is True:
    - /<ADMIN_URL>/... is allowed (so we can turn it off)
    - /api/health/... is allowed
    - static/media/uploads are allowed
    - /api/* returns 503 JSON (except health)
    - other pages return maintenance HTML (503)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_bypass(request.path):
            return self.get_response(request)

        enabled, message, scheduled_end = self._get_maintenance_state()
        if not enabled:
            return self.get_response(request)

        if request.path.startswith("/api/"):
            return JsonResponse(
                {"ok": False, "error": "maintenance", "message": "メンテナンス中です。しばらくしてから再度お試しください。"},
                status=503,
            )

        response = render(
            request,
            "frontend/maintenance.html",
            {
                "message": message,
                "scheduled_end": scheduled_end,
            },
            status=503,
        )
        response["Retry-After"] = "300"
        return response

    def _should_bypass(self, path: str) -> bool:
        admin_url = getattr(settings, "ADMIN_URL", "admin").strip("/")
        admin_prefix = f"/{admin_url}/"

        if path.startswith(admin_prefix):
            return True

        # Explicit maintenance page (optional preview / direct access)
        if path == "/maintenance/":
            return True

        # Health must stay up for orchestration / monitoring
        if path.startswith("/api/health/"):
            return True

        # Static/media must remain accessible
        if path.startswith("/static/") or path.startswith("/uploads/"):
            return True

        # Allow favicon
        if path in ("/favicon.ico",):
            return True

        return False

    def _get_maintenance_state(self):
        # Lazy import to avoid app-loading issues
        try:
            from frontend.models import SiteMaintenance
        except Exception:
            return False, "", None

        try:
            s = SiteMaintenance.get_solo()
            return bool(s.enabled), (s.message or ""), s.scheduled_end
        except Exception:
            # Fail open (do not block) if DB is not ready
            return False, "", None


