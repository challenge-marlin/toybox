"""
URL configuration for ToyBox project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from frontend.views import AnnouncementsView
import frontend.views as frontend_views
# まず、すべてのadmin.pyファイルをインポートしてモデルを登録
# これにより、admin.siteにすべてのモデルが登録されます
import users.admin  # noqa: F401
# 他のadmin.pyファイルも必要に応じてインポート
# import gamification.admin  # noqa: F401
# import submissions.admin  # noqa: F401

from .admin_site import CustomAdminSite

# カスタム管理サイトを作成
# 注意: 上記のインポートにより、admin.siteにすべてのモデルが登録されています
custom_admin_site = CustomAdminSite(name='admin')

# 既存のadmin.siteからすべてのモデル登録をカスタムサイトにコピー
for model, admin_class in admin.site._registry.items():
    # 既存のAdminクラスのインスタンスをそのまま使用
    custom_admin_site._registry[model] = admin_class
    # Adminクラスのadmin_site属性を更新
    admin_class.admin_site = custom_admin_site

# 既存のadmin.siteをカスタムサイトに置き換え
admin.site = custom_admin_site

# Django管理サイトの日本語化（CustomAdminSiteで既に設定済み）
# admin.site.site_header = 'ToyBox 管理サイト'
# admin.site.site_title = 'ToyBox 管理'
# admin.site.index_title = 'サイト管理'
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
    SPECTACULAR_AVAILABLE = True
except ImportError:
    SPECTACULAR_AVAILABLE = False

urlpatterns = [
    # Admin panel (custom admin UI) - Must be before admin.site.urls
    path('admin/console/', include('adminpanel.urls')),
    
    # Django admin site (custom admin site)
    path('admin/', custom_admin_site.urls),
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
    path('api/user/profile/<str:anon_id>/', user_views.ProfileGetView.as_view(), name='user-profile-get'),
    path('api/user/profile/upload', user_views.ProfileUploadView.as_view(), name='user-profile-upload'),
    path('api/cards/', include('gamification.urls')),
    path('api/', include('submissions.urls')),
    path('api/', include('lottery.urls')),
    path('api/share/', include('sharing.urls')),
    path('api/announcements/', AnnouncementsView.as_view(), name='announcements'),
    path('api/contact/', frontend_views.ContactView.as_view(), name='contact'),
    path('api/inquiry/', frontend_views.InquiryView.as_view(), name='inquiry'),
    
    # Admin API endpoints
    path('api/', include('adminpanel.urls')),
    
    # Frontend (Django templates)
    path('', include('frontend.urls')),
]

# Media files serving
from toybox.media import get_media_urlpatterns
urlpatterns += get_media_urlpatterns()

# Static files serving (for static files only, not media)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

