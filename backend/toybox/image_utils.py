"""
画像URL生成とファイル存在確認の統一ユーティリティ
"""
import os
import logging
from pathlib import Path
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def build_https_absolute_uri(request, path):
    """
    HTTPSを強制した絶対URLを構築する
    
    Args:
        request: Django requestオブジェクト
        path: 相対パスまたは絶対URL
    
    Returns:
        HTTPSの絶対URL
    """
    try:
        # まず通常の方法で絶対URLを構築
        absolute_url = request.build_absolute_uri(path)
        
        # HTTPをHTTPSに置き換え
        if absolute_url.startswith('http://'):
            absolute_url = absolute_url.replace('http://', 'https://', 1)
        
        return absolute_url
    except Exception as e:
        logger.warning(f'Failed to build HTTPS absolute URI for {path}: {e}')
        # フォールバック: 相対パスの場合、HTTPSベースURLを構築
        if path.startswith('/'):
            from django.conf import settings
            # プロダクション設定からHTTPSベースURLを取得
            if hasattr(settings, 'MEDIA_URL') and settings.MEDIA_URL.startswith('https://'):
                base_url = settings.MEDIA_URL.rstrip('/')
                return f"{base_url}{path}"
            # デフォルトのHTTPS URL
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
                if not os.path.exists(image_field.path):
                    logger.warning(f'Image file not found: {image_field.path}')
                    return None
            
            image_url = image_field.url
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
                        image_url = optimized_url
                except Exception as e:
                    logger.debug(f'Failed to get optimized image URL: {e}')
            
            if request:
                return build_https_absolute_uri(request, image_url)
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
            
            # 既に絶対URLの場合、HTTPをHTTPSに置き換え（同じドメインの場合のみ）
            if image_url.startswith('http://') or image_url.startswith('https://'):
                # HTTPをHTTPSに置き換え（同じドメインの場合のみ）
                if image_url.startswith('http://toybox.ayatori-inc.co.jp'):
                    result_url = image_url.replace('http://', 'https://', 1)
                    logger.debug(f'Converted HTTP to HTTPS: {result_url}')
                    return result_url
                logger.debug(f'Returning absolute URL as-is: {image_url}')
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

