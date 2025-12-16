"""
StudySphere SSO integration utilities.
チケット発行・検証型のSSO連携を実装します。
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# StudySphere API設定（仮 - 返信待ち）
# TODO: 実際の値が返ってきたらコメントアウトを外して設定してください
# STUDYSPHERE_API_BASE_URL = 'https://api.studysphere.example.com'
# STUDYSPHERE_FRONTEND_URL = 'https://studysphere.example.com'
# STUDYSPHERE_SERVICE_TOKEN = 'your-service-token-here'


def verify_ticket(ticket):
    """
    StudySphereのチケットを検証し、ユーザー情報を取得します。
    
    Args:
        ticket: StudySphereから受け取ったチケット文字列
        
    Returns:
        dict: {
            'valid': bool,  # チケットが有効かどうか
            'studysphere_user_id': str,  # StudySphereのユーザーID（外部ID）
            'error': str,  # エラーメッセージ（valid=Falseの場合）
            'error_code': str,  # エラーコード（ALREADY_USED, EXPIREDなど）
        }
    """
    # TODO: 実際のAPI Base URLが返ってきたらコメントアウトを外してください
    api_base_url = getattr(settings, 'STUDYSPHERE_API_BASE_URL', None)
    service_token = getattr(settings, 'STUDYSPHERE_SERVICE_TOKEN', None)
    
    if not api_base_url or not service_token:
        logger.warning('StudySphere API設定が未設定です。仮のレスポンスを返します。')
        # 開発用の仮レスポンス（実際の実装時は削除）
        return {
            'valid': False,
            'error': 'StudySphere API設定が未設定です',
            'error_code': 'CONFIG_ERROR',
        }
    
    # チケット検証APIを呼び出す
    verify_url = f'{api_base_url}/api/sso/ticket/verify'
    headers = {
        'Authorization': f'Bearer {service_token}',
        'Content-Type': 'application/json',
    }
    data = {
        'ticket': ticket,
    }
    
    try:
        response = requests.post(verify_url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('valid') is True:
                return {
                    'valid': True,
                    'studysphere_user_id': result.get('studysphere_user_id'),
                }
            else:
                return {
                    'valid': False,
                    'error': result.get('error', 'チケットが無効です'),
                    'error_code': result.get('error_code', 'INVALID'),
                }
        elif response.status_code == 400:
            # 既に使用済みまたは期限切れ
            result = response.json()
            return {
                'valid': False,
                'error': result.get('error', 'チケットが無効です'),
                'error_code': result.get('error_code', 'INVALID'),
            }
        else:
            logger.error(f'StudySphere ticket verification failed: {response.status_code} - {response.text}')
            return {
                'valid': False,
                'error': 'チケット検証に失敗しました',
                'error_code': 'VERIFICATION_ERROR',
            }
    except requests.exceptions.RequestException as e:
        logger.error(f'StudySphere API request failed: {str(e)}')
        return {
            'valid': False,
            'error': 'StudySphere APIへの接続に失敗しました',
            'error_code': 'API_ERROR',
        }


def get_studysphere_login_url(return_url=None):
    """
    StudySphereのSSOログインURLを生成します。
    
    Args:
        return_url: SSO認証後のリダイレクト先URL（ToyBoxのコールバックURL）
        
    Returns:
        str: StudySphereのSSOログインURL
    """
    # TODO: 実際のフロントエンドURLが返ってきたらコメントアウトを外してください
    frontend_url = getattr(settings, 'STUDYSPHERE_FRONTEND_URL', None)
    
    if not frontend_url:
        logger.warning('StudySphere Frontend URLが未設定です。')
        return None
    
    # コールバックURLを構築
    if not return_url:
        from django.conf import settings
        # デフォルトのコールバックURL
        return_url = f'{settings.SITE_URL or "http://localhost:8000"}/sso/callback/'
    
    # StudySphereのSSOログインURLを構築
    # 実際の実装では、StudySphereの仕様に合わせてURLを構築してください
    login_url = f'{frontend_url}/sso/login?return_url={return_url}'
    
    return login_url
