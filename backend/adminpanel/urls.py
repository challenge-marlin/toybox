"""
Adminpanel app URLs for DRF - Admin API and Admin UI.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import template_views

router = DefaultRouter()
router.register(r'admin/users', views.AdminUserViewSet, basename='admin-user')
router.register(r'admin/submissions', views.AdminSubmissionViewSet, basename='admin-submission')
router.register(r'admin/discord-shares', views.AdminDiscordShareViewSet, basename='admin-discord-share')
router.register(r'admin/audit-logs', views.AdminAuditLogViewSet, basename='admin-audit-log')

urlpatterns = [
    # Admin UI (Django templates) - Must be before API endpoints
    # Note: These paths are included under 'admin/console/' in toybox/urls.py
    # So we don't include 'admin/console/' prefix here
    path('', template_views.dashboard, name='admin-dashboard'),
    path('users/', template_views.user_list, name='admin-user-list'),
    path('users/<int:user_id>/', template_views.user_detail, name='admin-user-detail'),
    path('submissions/', template_views.submission_list, name='admin-submission-list'),
    path('discord-shares/', template_views.discord_share_list, name='admin-discord-share-list'),
    path('discord-post/', template_views.discord_share_list, name='admin-discord-post-list'),  # Alias for discord-shares
    path('discord-bot-post/', template_views.discord_bot_post, name='admin-discord-bot-post'),  # Discord bot post page
    path('audit-logs/', template_views.audit_log_list, name='admin-audit-log-list'),
    
    # API endpoints (must be after template views to avoid conflicts)
    path('api/', include(router.urls)),
    path('api/admin/discord-bot-post/', views.DiscordBotPostView.as_view(), name='admin-discord-bot-post-api'),
]
