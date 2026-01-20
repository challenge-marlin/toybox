"""
画像最適化ユーティリティ
画像をJPG形式に変換し、サイズと品質を最適化します
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning('PIL/Pillow is not available. Image optimization will be disabled.')


def optimize_image_to_jpg(
    image_file,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    quality: int = 85,
    preserve_alpha: bool = False
) -> Optional[BytesIO]:
    """
    画像をJPG形式に最適化して返す
    
    Args:
        image_file: 画像ファイルオブジェクト（ファイルパス、BytesIO、またはファイルオブジェクト）
        max_width: 最大幅（Noneの場合はリサイズしない）
        max_height: 最大高さ（Noneの場合はリサイズしない）
        quality: JPG品質（1-100、デフォルト85）
        preserve_alpha: アルファチャンネルを保持するか（Trueの場合はPNGとして保存）
    
    Returns:
        BytesIO: 最適化された画像データ、またはNone（エラー時）
    """
    if not PIL_AVAILABLE:
        logger.warning('PIL/Pillow is not available. Cannot optimize image.')
        return None
    
    try:
        # ファイルを開く
        if isinstance(image_file, (str, Path)):
            img = Image.open(image_file)
        elif hasattr(image_file, 'read'):
            img = Image.open(image_file)
            image_file.seek(0)  # リセット
        else:
            logger.error(f'Invalid image_file type: {type(image_file)}')
            return None
        
        # RGBAモードに変換（アルファチャンネル対応）
        if img.mode in ('RGBA', 'LA', 'P'):
            if preserve_alpha:
                # アルファチャンネルを保持する場合はPNGとして保存
                output = BytesIO()
                img.save(output, format='PNG', optimize=True)
                output.seek(0)
                return output
            else:
                # アルファチャンネルを削除してRGBに変換
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # EXIF情報を削除して向きを修正
        img = ImageOps.exif_transpose(img)
        
        # リサイズ（必要に応じて）
        if max_width or max_height:
            img.thumbnail((max_width or img.width, max_height or img.height), Image.Resampling.LANCZOS)
        
        # JPGとして保存
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output
    
    except Exception as e:
        logger.error(f'Failed to optimize image: {e}', exc_info=True)
        return None


def convert_and_save_image(
    source_path: str,
    target_path: str,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    quality: int = 85,
    preserve_original: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    画像をJPGに変換して保存する
    
    Args:
        source_path: 元の画像ファイルパス（MEDIA_ROOTからの相対パスまたは絶対パス）
        target_path: 保存先パス（MEDIA_ROOTからの相対パス）
        max_width: 最大幅
        max_height: 最大高さ
        quality: JPG品質
        preserve_original: 元のファイルを保持するか
    
    Returns:
        tuple: (success: bool, saved_path: str or None)
    """
    if not PIL_AVAILABLE:
        logger.warning('PIL/Pillow is not available. Cannot convert image.')
        return False, None
    
    try:
        # ソースファイルのパスを解決
        if os.path.isabs(source_path):
            source_full_path = source_path
        else:
            source_full_path = os.path.join(settings.MEDIA_ROOT, source_path)
        
        if not os.path.exists(source_full_path):
            logger.warning(f'Source file not found: {source_full_path}')
            return False, None
        
        # 画像を最適化
        optimized_data = optimize_image_to_jpg(
            source_full_path,
            max_width=max_width,
            max_height=max_height,
            quality=quality
        )
        
        if not optimized_data:
            logger.error(f'Failed to optimize image: {source_full_path}')
            return False, None
        
        # 保存
        target_full_path = default_storage.save(target_path, ContentFile(optimized_data.read()))
        
        logger.info(f'Converted image: {source_path} -> {target_full_path}')
        return True, target_full_path
    
    except Exception as e:
        logger.error(f'Failed to convert and save image: {e}', exc_info=True)
        return False, None


def get_optimized_image_url(
    original_url: str,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    quality: int = 85
) -> Optional[str]:
    """
    最適化された画像URLを取得する（存在しない場合は生成）
    
    Args:
        original_url: 元の画像URL
        max_width: 最大幅
        max_height: 最大高さ
        quality: JPG品質
    
    Returns:
        str: 最適化された画像URL、またはNone（元のURLを返す）
    """
    try:
        from urllib.parse import urlparse
        from toybox.image_utils import _get_file_path_from_url
        
        # URLからファイルパスを取得
        parsed = urlparse(original_url)
        original_path = parsed.path
        
        # ファイルパスを解決
        file_path = _get_file_path_from_url(original_path)
        if not file_path or not file_path.exists():
            logger.debug(f'Original file not found: {original_path}')
            return None
        
        # 既にJPGの場合はそのまま返す
        if file_path.suffix.lower() in ('.jpg', '.jpeg'):
            return original_url
        
        # 最適化されたファイルのパスを生成
        optimized_filename = f"{file_path.stem}_opt.jpg"
        optimized_relative_path = file_path.relative_to(Path(settings.MEDIA_ROOT))
        optimized_dir = optimized_relative_path.parent
        optimized_path = optimized_dir / optimized_filename
        
        # 最適化されたファイルが存在するか確認
        optimized_full_path = Path(settings.MEDIA_ROOT) / optimized_path
        if optimized_full_path.exists():
            # 既に存在する場合はURLを返す
            optimized_url = original_url.replace(file_path.name, optimized_filename)
            return optimized_url
        
        # 最適化されたファイルを生成
        success, saved_path = convert_and_save_image(
            str(file_path),
            str(optimized_path),
            max_width=max_width,
            max_height=max_height,
            quality=quality,
            preserve_original=True
        )
        
        if success:
            optimized_url = original_url.replace(file_path.name, optimized_filename)
            return optimized_url
        
        # 最適化に失敗した場合は元のURLを返す
        return original_url
    
    except Exception as e:
        logger.debug(f'Failed to get optimized image URL: {e}')
        return None
