"""
画像URL生成とファイル存在確認の統一ユーティリティ
"""
import os
import logging
from pathlib import Path
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def _is_local_host(host: str) -> bool:
    """リクエストホストがローカルかどうか（localhost / 127.0.0.1 等）"""
    if not host:
        return False
    h = host.split(':')[0].lower()
    return h in ('localhost', '127.0.0.1', '::1', '0.0.0.0')


def build_https_absolute_uri(request, path):
    """
    HTTPSを強制した絶対URLを構築する。
    ローカル環境（localhost / 127.0.0.1）のときはリクエストのスキームを使い、
    絶対URL（本番ドメイン等）が渡された場合はリクエストホスト基準のURLに差し替える。
    
    Args:
        request: Django requestオブジェクト
        path: 相対パス（/uploads/...）または絶対URL
    
    Returns:
        絶対URL（ローカル時はリクエストホスト基準）
    """
    try:
        use_path = path
        if isinstance(path, str) and (path.startswith('http://') or path.startswith('https://')):
            from urllib.parse import urlparse
            parsed = urlparse(path)
            use_path = parsed.path or '/'
            # ローカルでない場合は渡された絶対URLをそのまま使用
            if not _is_local_host(request.get_host()):
                if path.startswith('http://'):
                    return path.replace('http://', 'https://', 1)
                return path

        absolute_url = request.build_absolute_uri(use_path)
        # ローカル環境ではHTTPS強制しない（証明書未設定で表示崩れを防ぐ）
        if _is_local_host(request.get_host()):
            return absolute_url
        if absolute_url.startswith('http://'):
            absolute_url = absolute_url.replace('http://', 'https://', 1)
        return absolute_url
    except Exception as e:
        logger.warning(f'Failed to build HTTPS absolute URI for {path}: {e}')
        if isinstance(path, str) and path.startswith('/'):
            if hasattr(settings, 'MEDIA_URL') and settings.MEDIA_URL.startswith('https://'):
                return f"{settings.MEDIA_URL.rstrip('/')}{path}"
            return f"https://toybox.ayatori-inc.co.jp{path}"
        return path


def get_image_url(
    image_field=None,
    image_url_field: Optional[str] = None,
    request=None,
    verify_exists: bool = True,
    use_optimized: bool = True
) -> Optional[str]:
    """
    画像URLを取得する（統一的な処理）
    
    Args:
        image_field: DjangoのImageFieldインスタンス
        image_url_field: 画像URL文字列（相対パスまたは絶対URL）
        request: Django requestオブジェクト（絶対URL生成用）
        verify_exists: ファイルの存在確認を行うか
        use_optimized: 最適化された画像を使用するか（デフォルトTrue）
    
    Returns:
        画像URL（絶対URL）またはNone
    """
    # 1. ImageFieldを優先
    if image_field:
        try:
            if verify_exists and hasattr(image_field, 'path'):
                try:
                    if not os.path.exists(image_field.path):
                        logger.warning(f'Image file not found: {image_field.path}')
                        return None
                except Exception:
                    # リモートストレージ（S3等）では path が使えない場合がある
                    pass

            image_url = image_field.url
            logger.debug(f'[get_image_url] ImageField.url returned: {image_url}')
            
            # /media/ を /uploads/ に変換（互換性のため）
            if image_url.startswith('/media/'):
                image_url = image_url.replace('/media/', '/uploads/', 1)
                logger.debug(f'[get_image_url] Converted /media/ to /uploads/: {image_url}')
            
            # 最適化された画像を使用する場合
            if use_optimized:
                try:
                    from toybox.image_optimizer import get_optimized_image_url
                    optimized_url = get_optimized_image_url(
                        image_url,
                        max_width=None,
                        max_height=None,
                        quality=85
                    )
                    if optimized_url:
                        logger.debug(f'[get_image_url] Optimized URL: {optimized_url}')
                        image_url = optimized_url
                except Exception as e:
                    logger.debug(f'Failed to get optimized image URL: {e}')
            
            if request:
                result_url = build_https_absolute_uri(request, image_url)
                logger.debug(f'[get_image_url] Final URL after build_https_absolute_uri: {result_url}')
                return result_url
            logger.debug(f'[get_image_url] No request, returning: {image_url}')
            return image_url
        except (ValueError, AttributeError, OSError) as e:
            logger.warning(f'Failed to get image URL from ImageField: {e}')
            return None
    
    # 2. image_urlフィールドを確認
    if image_url_field:
        try:
            image_url = image_url_field.strip() if isinstance(image_url_field, str) else str(image_url_field)
            if not image_url:
                logger.debug(f'Empty image_url_field: {image_url_field}')
                return None
            
            logger.debug(f'Processing image_url_field: {image_url}')
            
            # 既に絶対URLの場合: request があれば build に通す（ローカル時はリクエストホストへ差し替え）
            if image_url.startswith('http://') or image_url.startswith('https://'):
                if request:
                    return build_https_absolute_uri(request, image_url)
                if image_url.startswith('http://toybox.ayatori-inc.co.jp'):
                    return image_url.replace('http://', 'https://', 1)
                return image_url
            
            # 相対パスの場合、絶対URLに変換
            if image_url.startswith('/'):
                if verify_exists:
                    # 相対パスからファイルパスを取得
                    file_path = _get_file_path_from_url(image_url)
                    if file_path and not file_path.exists():
                        logger.warning(f'Image file not found: {file_path}')
                        return None
                
                if request:
                    result_url = build_https_absolute_uri(request, image_url)
                    logger.debug(f'Built absolute URL from request: {result_url}')
                    return result_url
                else:
                    # requestがNoneの場合でも絶対URLを返す
                    # settings.MEDIA_URLを使用するか、デフォルトのHTTPS URLを構築
                    try:
                        if hasattr(settings, 'MEDIA_URL') and settings.MEDIA_URL:
                            base_url = str(settings.MEDIA_URL).rstrip('/')
                            # MEDIA_URLが既にパスを含んでいる場合（例: https://toybox.ayatori-inc.co.jp/uploads/）、重複を避ける
                            if base_url.endswith('/uploads') and image_url.startswith('/uploads/'):
                                # /uploads/ を削除して結合
                                relative_path = image_url.replace('/uploads/', '')
                                result_url = f"{base_url}/{relative_path}"
                                logger.debug(f'Built URL with MEDIA_URL (stripped): {result_url}')
                                return result_url
                            # 通常の結合（相対パスが / で始まる場合）
                            if image_url.startswith('/'):
                                result_url = f"{base_url}{image_url}"
                                logger.debug(f'Built URL with MEDIA_URL: {result_url}')
                                return result_url
                            # 相対パスが / で始まらない場合
                            result_url = f"{base_url}/{image_url}"
                            logger.debug(f'Built URL with MEDIA_URL (added slash): {result_url}')
                            return result_url
                    except Exception as e:
                        logger.warning(f'Failed to build absolute URL from MEDIA_URL: {e}')
                    # フォールバック: デフォルトのHTTPS URL
                    result_url = f"https://toybox.ayatori-inc.co.jp{image_url}"
                    logger.debug(f'Using fallback URL: {result_url}')
                    return result_url
            else:
                # 相対パスでも / で始まらない場合（通常は発生しない）
                logger.warning(f'Unexpected image_url format: {image_url}')
                return None
        except Exception as e:
            logger.warning(f'Failed to process image_url: {e}', exc_info=True)
            return None
    
    return None


# 称号画像フォールバック（ファイル未配置時）
TITLE_IMAGE_FALLBACK_PATH = '/static/frontend/hero/toybox-title.png'


def get_title_image_url(title_obj, request):
    """
    称号のバナー画像URLを取得する。ファイルが存在しない場合はフォールバック画像を返す。
    
    Args:
        title_obj: gamification.models.Title インスタンス
        request: Django request（絶対URL生成用）
    
    Returns:
        絶対URL（常に有効な画像を指す）
    """
    url = get_image_url(
        image_field=title_obj.image,
        image_url_field=title_obj.image_url,
        request=request,
        verify_exists=True,
        use_optimized=False,
    )
    if url:
        return url
    if request:
        return build_https_absolute_uri(request, TITLE_IMAGE_FALLBACK_PATH)
    return TITLE_IMAGE_FALLBACK_PATH


def _get_file_path_from_url(url: str) -> Optional[Path]:
    """
    URLからファイルパスを取得
    
    Args:
        url: 画像URL（相対パスまたは絶対URL）
    
    Returns:
        ファイルパスまたはNone
    """
    try:
        # 絶対URLの場合、パス部分を抽出
        if url.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url = parsed.path
        
        # /uploads/ から始まる場合
        if url.startswith('/uploads/'):
            # /uploads/ を削除
            relative_path = url.replace('/uploads/', '')
            media_root = Path(settings.MEDIA_ROOT)
            return media_root / relative_path
        
        # 相対パスの場合
        if url.startswith('/'):
            # 先頭の / を削除
            relative_path = url.lstrip('/')
            media_root = Path(settings.MEDIA_ROOT)
            return media_root / relative_path
        
        return None
    except Exception as e:
        logger.warning(f'Failed to get file path from URL: {e}')
        return None


def verify_image_file_exists(url: str) -> bool:
    """
    画像ファイルが存在するか確認
    
    Args:
        url: 画像URL（相対パスまたは絶対URL）
    
    Returns:
        ファイルが存在する場合True
    """
    try:
        file_path = _get_file_path_from_url(url)
        if file_path:
            return file_path.exists()
        return False
    except Exception as e:
        logger.warning(f'Failed to verify image file: {e}')
        return False


def clean_invalid_image_url(instance, field_name: str, url_field_name: str = None):
    """
    無効な画像URLをデータベースから削除
    
    Args:
        instance: モデルインスタンス
        field_name: ImageFieldのフィールド名
        url_field_name: image_urlフィールド名（オプション）
    """
    try:
        # ImageFieldをチェック
        image_field = getattr(instance, field_name, None)
        if image_field:
            if hasattr(image_field, 'path') and not os.path.exists(image_field.path):
                logger.info(f'Cleaning invalid ImageField: {field_name} for {instance}')
                setattr(instance, field_name, None)
                instance.save(update_fields=[field_name])
        
        # image_urlフィールドをチェック
        if url_field_name:
            image_url = getattr(instance, url_field_name, None)
            if image_url:
                if not verify_image_file_exists(image_url):
                    logger.info(f'Cleaning invalid image_url: {url_field_name} for {instance}')
                    setattr(instance, url_field_name, None)
                    instance.save(update_fields=[url_field_name])
    except Exception as e:
        logger.warning(f'Failed to clean invalid image URL: {e}')

