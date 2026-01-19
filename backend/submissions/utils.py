"""
Submissions app utilities for file handling and URL generation.
"""
import os
from pathlib import Path
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


def ensure_directory_exists(file_path):
    """
    ファイルパスのディレクトリが存在することを確認し、存在しない場合は作成する
    
    Args:
        file_path: ファイルパス（絶対パスまたはMEDIA_ROOTからの相対パス）
    
    Returns:
        bool: ディレクトリが存在するか作成できた場合True
    """
    try:
        if os.path.isabs(file_path):
            dir_path = os.path.dirname(file_path)
        else:
            # MEDIA_ROOTからの相対パスとして扱う
            dir_path = os.path.dirname(os.path.join(settings.MEDIA_ROOT, file_path))
        
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f'Failed to create directory {dir_path}: {str(e)}', exc_info=True)
        return False


def save_file_safely(file, relative_path):
    """
    ファイルを安全に保存する（ディレクトリ作成、エラーハンドリング含む）
    
    Args:
        file: アップロードされたファイルオブジェクト
        relative_path: MEDIA_ROOTからの相対パス（例: 'submissions/user_123_timestamp.png'）
    
    Returns:
        tuple: (success: bool, saved_path: str or None, error_message: str or None)
    """
    try:
        # ディレクトリの存在確認と作成
        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        if not ensure_directory_exists(full_path):
            return False, None, 'Failed to create directory'
        
        # ファイルを保存
        saved_path = default_storage.save(relative_path, ContentFile(file.read()))
        
        # 保存後の存在確認
        if default_storage.exists(saved_path):
            logger.info(f'File saved successfully: {saved_path}')
            return True, saved_path, None
        else:
            logger.error(f'File save reported success but file does not exist: {saved_path}')
            return False, None, 'File save verification failed'
    
    except Exception as e:
        logger.error(f'Failed to save file {relative_path}: {str(e)}', exc_info=True)
        return False, None, str(e)


def normalize_url_path(path):
    """
    URLパスを正規化する（スラッシュの統一、パスのクリーンアップ）
    
    Args:
        path: URLパス
    
    Returns:
        str: 正規化されたURLパス
    """
    if not path:
        return ''
    
    # バックスラッシュをスラッシュに変換
    path = path.replace('\\', '/')
    
    # 連続するスラッシュを1つに
    while '//' in path:
        path = path.replace('//', '/')
    
    # 先頭のスラッシュを保持（絶対パスの場合）
    if path.startswith('/'):
        return path
    else:
        return '/' + path


def build_file_url(request, relative_path, base_path='/uploads/'):
    """
    ファイルURLを構築する（相対URLと絶対URLの両方をサポート、HTTPSを強制）
    
    Args:
        request: Django requestオブジェクト
        relative_path: MEDIA_ROOTからの相対パス
        base_path: URLベースパス（デフォルト: '/uploads/'）
    
    Returns:
        str: ファイルURL（HTTPSの絶対URL）
    """
    from toybox.image_utils import build_https_absolute_uri
    
    # パスを正規化
    relative_path = normalize_url_path(relative_path)
    
    # base_pathから相対パスを抽出（既にbase_pathが含まれている場合）
    if relative_path.startswith(base_path):
        url_path = relative_path
    else:
        # base_pathを追加
        url_path = base_path.rstrip('/') + '/' + relative_path.lstrip('/')
    
    # HTTPSを強制した絶対URLを構築
    try:
        absolute_url = build_https_absolute_uri(request, url_path)
        return absolute_url
    except Exception as e:
        logger.error(f'Failed to build absolute URL for {url_path}: {str(e)}', exc_info=True)
        # フォールバック: 相対URLを返す
        return url_path


def verify_file_exists(file_path_or_url):
    """
    ファイルが存在することを確認する
    
    Args:
        file_path_or_url: ファイルパスまたはURL
    
    Returns:
        bool: ファイルが存在する場合True
    """
    try:
        # URLの場合はパスに変換
        if file_path_or_url.startswith('http://') or file_path_or_url.startswith('https://'):
            # URLからパスを抽出（簡易実装）
            url_path = file_path_or_url.split('/uploads/', 1)[-1] if '/uploads/' in file_path_or_url else None
            if url_path:
                file_path = os.path.join(settings.MEDIA_ROOT, url_path)
            else:
                return False
        elif file_path_or_url.startswith('/'):
            # 絶対パスまたはURLパス
            if file_path_or_url.startswith('/uploads/'):
                file_path = os.path.join(settings.MEDIA_ROOT, file_path_or_url.replace('/uploads/', '', 1))
            else:
                file_path = file_path_or_url
        else:
            # 相対パス（MEDIA_ROOTからの）
            file_path = os.path.join(settings.MEDIA_ROOT, file_path_or_url)
        
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    except Exception as e:
        logger.error(f'Failed to verify file existence for {file_path_or_url}: {str(e)}', exc_info=True)
        return False


def get_submission_file_url(submission, request=None):
    """
    Submissionオブジェクトから適切なファイルURLを取得する
    
    Args:
        submission: Submissionオブジェクト
        request: Django requestオブジェクト（絶対URL生成用、オプション）
    
    Returns:
        dict: {
            'imageUrl': str or None,
            'videoUrl': str or None,
            'gameUrl': str or None,
            'displayImageUrl': str or None,
            'thumbnailUrl': str or None
        }
    """
    result = {
        'imageUrl': None,
        'videoUrl': None,
        'gameUrl': None,
        'displayImageUrl': None,
        'thumbnailUrl': None
    }
    
    from toybox.image_utils import build_https_absolute_uri
    
    # サムネイル（ゲームの場合）
    if submission.thumbnail:
        try:
            if request:
                result['thumbnailUrl'] = build_https_absolute_uri(request, submission.thumbnail.url)
                result['displayImageUrl'] = result['thumbnailUrl']
            else:
                thumbnail_url = submission.thumbnail.url
                # HTTPをHTTPSに置き換え
                if thumbnail_url.startswith('http://'):
                    thumbnail_url = thumbnail_url.replace('http://', 'https://', 1)
                result['thumbnailUrl'] = thumbnail_url
                result['displayImageUrl'] = result['thumbnailUrl']
        except Exception as e:
            logger.error(f'Failed to get thumbnail URL: {str(e)}', exc_info=True)
    
    # 画像
    if submission.image:
        try:
            if request:
                result['imageUrl'] = build_https_absolute_uri(request, submission.image.url)
                if not result['displayImageUrl']:
                    result['displayImageUrl'] = result['imageUrl']
            else:
                image_url = submission.image.url
                # HTTPをHTTPSに置き換え
                if image_url.startswith('http://'):
                    image_url = image_url.replace('http://', 'https://', 1)
                result['imageUrl'] = image_url
                if not result['displayImageUrl']:
                    result['displayImageUrl'] = result['imageUrl']
        except Exception as e:
            logger.error(f'Failed to get image URL: {str(e)}', exc_info=True)
    
    # image_url（レガシーまたは外部URL）
    if submission.image_url:
        image_url = submission.image_url
        # HTTPをHTTPSに置き換え（同じドメインの場合のみ）
        if image_url.startswith('http://toybox.ayatori-inc.co.jp'):
            image_url = image_url.replace('http://', 'https://', 1)
        result['imageUrl'] = image_url
        if not result['displayImageUrl']:
            result['displayImageUrl'] = image_url
    
    # 動画
    if submission.video_url:
        result['videoUrl'] = submission.video_url
    
    # ゲーム
    if submission.game_url:
        result['gameUrl'] = submission.game_url
    
    return result


def audit_zip_file(zip_path):
    """
    ZIPファイルの内容を監査し、怪しいファイルがないかチェックする
    
    Args:
        zip_path: ZIPファイルのパス
    
    Returns:
        dict: {
            'is_safe': bool,
            'warnings': list[str],
            'errors': list[str],
            'has_index_html': bool,
            'suspicious_files': list[str],
            'web_files': list[str]
        }
    """
    import zipfile
    import os
    
    result = {
        'is_safe': True,
        'warnings': [],
        'errors': [],
        'has_index_html': False,
        'suspicious_files': [],
        'web_files': []
    }
    
    # 怪しいファイル拡張子のリスト
    # 注意: .jsはWebゲームに必須のため除外
    SUSPICIOUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.jar', '.app',
        '.dll', '.so', '.dylib', '.sys', '.drv', '.ocx', '.cpl', '.msi', '.msm',
        '.ps1', '.sh', '.bash', '.zsh', '.fish', '.py', '.pyc', '.pyo', '.pyd',
        '.php', '.asp', '.aspx', '.jsp', '.pl', '.rb', '.go', '.rs', '.c', '.cpp',
        '.deb', '.rpm', '.pkg', '.dmg', '.iso', '.img', '.bin', '.run'
    }
    
    # Webゲームに関連するファイル拡張子
    WEB_FILE_EXTENSIONS = {
        '.html', '.htm', '.css', '.js', '.json', '.xml', '.svg',
        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.bmp',
        '.mp3', '.mp4', '.webm', '.ogg', '.wav', '.flac',
        '.woff', '.woff2', '.ttf', '.eot', '.otf',
        '.txt', '.md', '.pdf'
    }
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # 各ファイルをチェック
            for file_name in file_list:
                # ディレクトリはスキップ
                if file_name.endswith('/'):
                    continue
                
                # ファイル名を小文字に変換して拡張子を取得
                file_lower = file_name.lower()
                file_ext = os.path.splitext(file_lower)[1]
                
                # index.htmlの存在確認
                if file_lower == 'index.html' or file_lower.endswith('/index.html'):
                    result['has_index_html'] = True
                    result['web_files'].append(file_name)
                    continue
                
                # Webゲームに関連するファイルかチェック
                if file_ext in WEB_FILE_EXTENSIONS:
                    result['web_files'].append(file_name)
                    continue
                
                # 怪しいファイル拡張子かチェック
                if file_ext in SUSPICIOUS_EXTENSIONS:
                    result['suspicious_files'].append(file_name)
                    result['warnings'].append(f'怪しいファイルが検出されました: {file_name}')
                    result['is_safe'] = False
                    continue
                
                # 拡張子がないファイルも警告
                if not file_ext and '.' not in os.path.basename(file_name):
                    result['warnings'].append(f'拡張子のないファイルが検出されました: {file_name}')
            
            # index.htmlがない場合はエラー
            if not result['has_index_html']:
                result['errors'].append('index.htmlが見つかりません。Webゲームにはindex.htmlが必要です。')
                result['is_safe'] = False
            
            # Webゲームに関連するファイルが少なすぎる場合は警告
            if len(result['web_files']) < 2:
                result['warnings'].append('Webゲームに関連するファイルが少なすぎます。')
                result['is_safe'] = False
            
            # 怪しいファイルが多すぎる場合はエラー
            if len(result['suspicious_files']) > 0:
                result['errors'].append(f'{len(result["suspicious_files"])}個の怪しいファイルが検出されました。')
                result['is_safe'] = False
            
    except zipfile.BadZipFile:
        result['errors'].append('ZIPファイルが破損しているか、無効な形式です。')
        result['is_safe'] = False
    except Exception as e:
        logger.error(f'Failed to audit ZIP file {zip_path}: {str(e)}', exc_info=True)
        result['errors'].append(f'ZIPファイルの監査中にエラーが発生しました: {str(e)}')
        result['is_safe'] = False
    
    return result






