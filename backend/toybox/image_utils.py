"""
画像URL生成とファイル存在確認の統一ユーティリティ
"""
import os
import logging
from pathlib import Path
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def get_image_url(
    image_field=None,
    image_url_field: Optional[str] = None,
    request=None,
    verify_exists: bool = True
) -> Optional[str]:
    """
    画像URLを取得する（統一的な処理）
    
    Args:
        image_field: DjangoのImageFieldインスタンス
        image_url_field: 画像URL文字列（相対パスまたは絶対URL）
        request: Django requestオブジェクト（絶対URL生成用）
        verify_exists: ファイルの存在確認を行うか
    
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
            
            if request:
                return request.build_absolute_uri(image_field.url)
            return image_field.url
        except (ValueError, AttributeError, OSError) as e:
            logger.warning(f'Failed to get image URL from ImageField: {e}')
            return None
    
    # 2. image_urlフィールドを確認
    if image_url_field:
        try:
            image_url = image_url_field.strip()
            if not image_url:
                return None
            
            # 相対パスの場合、絶対URLに変換
            if image_url.startswith('/'):
                if verify_exists:
                    # 相対パスからファイルパスを取得
                    file_path = _get_file_path_from_url(image_url)
                    if file_path and not file_path.exists():
                        logger.warning(f'Image file not found: {file_path}')
                        return None
                
                if request:
                    return request.build_absolute_uri(image_url)
                return image_url
            else:
                # 既に絶対URLの場合
                return image_url
        except Exception as e:
            logger.warning(f'Failed to process image_url: {e}')
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
            return settings.MEDIA_ROOT / relative_path
        
        # 相対パスの場合
        if url.startswith('/'):
            # 先頭の / を削除
            relative_path = url.lstrip('/')
            return settings.MEDIA_ROOT / relative_path
        
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

