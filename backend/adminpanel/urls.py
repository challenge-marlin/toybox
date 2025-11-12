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
    # API endpoints
    path('', include(router.urls)),
    
    # Admin UI (Django templates)
    path('admin/console/', template_views.dashboard, name='admin-dashboard'),
    path('admin/console/users/', template_views.user_list, name='admin-user-list'),
    path('admin/console/users/<int:user_id>/', template_views.user_detail, name='admin-user-detail'),
    path('admin/console/submissions/', template_views.submission_list, name='admin-submission-list'),
    path('admin/console/discord-shares/', template_views.discord_share_list, name='admin-discord-share-list'),
    path('admin/console/audit-logs/', template_views.audit_log_list, name='admin-audit-log-list'),
]
