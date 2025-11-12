"""
URL configuration for ToyBox project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    SPECTACULAR_AVAILABLE = True
except ImportError:
    SPECTACULAR_AVAILABLE = False

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
]

# API Schema (if drf-spectacular is installed)
if SPECTACULAR_AVAILABLE:
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]

urlpatterns += [
    # Health check (no auth required)
    path('api/health/', include('toybox.health.urls')),
    
    # General API endpoints
    path('api/auth/', include('users.urls')),
    path('api/users/', include('users.urls')),
    path('api/user/profile/', user_views.ProfileUpdateView.as_view(), name='user-profile'),
    path('api/user/profile/upload', user_views.ProfileUploadView.as_view(), name='user-profile-upload'),
    path('api/cards/', include('gamification.urls')),
    path('api/', include('submissions.urls')),
    path('api/', include('lottery.urls')),
    
    # Admin API endpoints
    path('api/', include('adminpanel.urls')),
    
    # Admin panel (custom admin UI)
    path('admin/console/', include('adminpanel.urls')),
    
    # Frontend (Django templates)
    path('', include('frontend.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve card images from static directory
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^uploads/cards/(?P<path>.*)$', serve, {'document_root': settings.BASE_DIR / 'frontend' / 'static' / 'frontend' / 'uploads' / 'cards'}),
    ]

