"""
Users app URLs for DRF.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'me/meta', views.UserMetaViewSet, basename='user-meta')

urlpatterns = [
    # Auth endpoints (already under /api/auth/ in main urls.py)
    path('login/', views.LoginView.as_view(), name='login'),
    path('refresh/', views.RefreshTokenView.as_view(), name='refresh'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Discord OAuth endpoints
    path('discord/login/', views.DiscordOAuthLoginView.as_view(), name='discord-login'),
    path('discord/callback/', views.DiscordOAuthCallbackView.as_view(), name='discord-callback'),
    path('discord/status/', views.DiscordStatusView.as_view(), name='discord-status'),
    
    # Current user endpoint
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Notification endpoints
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/read/', views.NotificationReadView.as_view(), name='notifications-read'),
    
    # Topic endpoints
    path('topic/generate/', views.TopicGenerateView.as_view(), name='topic-generate'),
    
    # Router URLs
    path('', include(router.urls)),
]
