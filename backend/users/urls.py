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
    
    # Current user endpoint
    path('me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Notification endpoints
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/read/', views.NotificationReadView.as_view(), name='notifications-read'),
    
    # Router URLs
    path('', include(router.urls)),
]
