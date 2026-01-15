"""
Adminpanel API URLs.

This file exists to avoid double-prefix issues like:
  /api/ + adminpanel.urls (which itself had /api/...) => /api/api/...

We mount this under /api/ in toybox/urls.py, so paths here should NOT start with /api/.
Expected endpoints:
  - /api/admin/users/
  - /api/admin/submissions/
  - /api/admin/discord-shares/
  - /api/admin/audit-logs/
  - /api/admin/discord-bot-post/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'admin/users', views.AdminUserViewSet, basename='admin-user')
router.register(r'admin/submissions', views.AdminSubmissionViewSet, basename='admin-submission')
router.register(r'admin/discord-shares', views.AdminDiscordShareViewSet, basename='admin-discord-share')
router.register(r'admin/audit-logs', views.AdminAuditLogViewSet, basename='admin-audit-log')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/discord-bot-post/', views.DiscordBotPostView.as_view(), name='admin-discord-bot-post-api'),
]



