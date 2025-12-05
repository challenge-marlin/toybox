"""
メディアファイル配信設定
開発環境と本番環境で統一された設定を提供
"""
from django.conf import settings
from django.views.static import serve
from django.urls import re_path, path
from django.views.decorators.cache import cache_control
from django.http import Http404
from django.views.static import serve as static_serve


def get_media_urlpatterns():
    """
    メディアファイル配信用のURLパターンを返す
    
    Returns:
        list: URLパターンのリスト
    """
    patterns = []
    
    if settings.DEBUG:
        # 開発環境: Djangoのserve()を使用してメディアファイルを配信
        
        def favicon_view(request):
            """Serve favicon.ico from static directory."""
            favicon_path = settings.BASE_DIR / 'frontend' / 'static' / 'frontend' / 'favicon.ico'
            if favicon_path.exists():
                return static_serve(request, 'favicon.ico', document_root=str(settings.BASE_DIR / 'frontend' / 'static' / 'frontend'))
            raise Http404("Favicon not found")
        
        patterns = [
            # カード画像
            re_path(
                r'^uploads/cards/(?P<path>.*)$',
                serve,
                {'document_root': str(settings.MEDIA_ROOT / 'cards')}
            ),
            # 提出物（画像・動画・サムネイル）
            re_path(
                r'^uploads/submissions/(?P<path>.*)$',
                serve,
                {'document_root': str(settings.MEDIA_ROOT / 'submissions')}
            ),
            # プロフィール画像（アバター・ヘッダー）
            re_path(
                r'^uploads/profiles/(?P<path>.*)$',
                serve,
                {'document_root': str(settings.MEDIA_ROOT / 'profiles')}
            ),
            # その他のアップロードファイル（フォールバック）
            re_path(
                r'^uploads/(?P<path>.*)$',
                serve,
                {'document_root': str(settings.MEDIA_ROOT)}
            ),
            # ゲームファイル（/media/パス互換性のため）
            re_path(
                r'^media/(?P<path>.*)$',
                serve,
                {'document_root': str(settings.MEDIA_ROOT)}
            ),
            # Favicon
            path(
                'favicon.ico',
                cache_control(max_age=86400)(favicon_view)
            ),
        ]
    else:
        # 本番環境: 通常はnginxやS3などの静的ファイルサーバーを使用
        # 必要に応じてここに設定を追加
        pass
    
    return patterns

