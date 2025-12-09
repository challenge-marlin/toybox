"""
Discord OAuth2 integration utilities.
"""
import requests
import logging
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import UserMeta

logger = logging.getLogger(__name__)


def get_discord_oauth_url(request=None, state=None):
    """
    Generate Discord OAuth2 authorization URL.
    
    Args:
        request: Django request object (optional, used to build redirect URI dynamically)
        state: Optional state parameter for CSRF protection
        
    Returns:
        str: Discord OAuth2 authorization URL
    """
    client_id = getattr(settings, 'DISCORD_CLIENT_ID', '')
    
    # リダイレクトURIを動的に生成（リクエストがある場合）
    if request:
        # /api/auth/discord/callback/ を直接使用（users.urlsが/api/auth/と/api/users/の両方にマウントされているため）
        redirect_uri = request.build_absolute_uri('/api/auth/discord/callback/')
    else:
        redirect_uri = getattr(settings, 'DISCORD_REDIRECT_URI', '')
    
    if not client_id or not redirect_uri:
        raise ValueError('DISCORD_CLIENT_ID and DISCORD_REDIRECT_URI must be set')
    
    # ログにリダイレクトURIを記録（デバッグ用）
    logger.info(f'Discord OAuth redirect URI: {redirect_uri}')
    
    scopes = ['identify', 'guilds', 'guilds.members.read']
    scope_string = ' '.join(scopes)
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': scope_string,
    }
    
    if state:
        params['state'] = state
    
    # URLエンコードを使用して正しくエンコードする
    url = 'https://discord.com/api/oauth2/authorize?' + urlencode(params)
    logger.info(f'Discord OAuth URL: {url}')
    return url


def exchange_discord_code(code, request=None):
    """
    Exchange Discord authorization code for access token.
    
    Args:
        code: Authorization code from Discord callback
        request: Django request object (optional, used to build redirect URI dynamically)
        
    Returns:
        dict: Token response containing access_token, refresh_token, expires_in, etc.
    """
    client_id = getattr(settings, 'DISCORD_CLIENT_ID', '')
    client_secret = getattr(settings, 'DISCORD_CLIENT_SECRET', '')
    
    # リダイレクトURIを動的に生成（リクエストがある場合）
    if request:
        # /api/auth/discord/callback/ を直接使用（users.urlsが/api/auth/と/api/users/の両方にマウントされているため）
        redirect_uri = request.build_absolute_uri('/api/auth/discord/callback/')
    else:
        redirect_uri = getattr(settings, 'DISCORD_REDIRECT_URI', '')
    
    if not client_id or not client_secret or not redirect_uri:
        raise ValueError('DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and DISCORD_REDIRECT_URI must be set')
    
    # ログにリダイレクトURIを記録（デバッグ用）
    logger.info(f'Discord token exchange redirect URI: {redirect_uri}')
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers, timeout=10)
    
    if response.status_code != 200:
        error_text = response.text
        try:
            error_json = response.json()
            error_message = error_json.get('error_description', error_json.get('error', error_text))
        except:
            error_message = error_text
        
        logger.error(f'Discord token exchange failed: {response.status_code} - {error_message}')
        logger.error(f'Request redirect_uri: {redirect_uri}')
        logger.error(f'Request data: client_id={client_id[:10]}..., redirect_uri={redirect_uri}')
        raise ValueError(f'Discord token exchange failed ({response.status_code}): {error_message}')
    
    return response.json()


def refresh_discord_token(refresh_token):
    """
    Refresh Discord access token using refresh token.
    
    Args:
        refresh_token: Discord refresh token
        
    Returns:
        dict: Token response containing access_token, refresh_token, expires_in, etc.
    """
    client_id = getattr(settings, 'DISCORD_CLIENT_ID', '')
    client_secret = getattr(settings, 'DISCORD_CLIENT_SECRET', '')
    
    if not client_id or not client_secret:
        raise ValueError('DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET must be set')
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    response = requests.post('https://discord.com/api/oauth2/token', data=data, headers=headers, timeout=10)
    
    if response.status_code != 200:
        logger.error(f'Discord token refresh failed: {response.status_code} - {response.text}')
        raise ValueError(f'Discord token refresh failed: {response.status_code}')
    
    return response.json()


def get_discord_user_info(access_token):
    """
    Get Discord user information using access token.
    
    Args:
        access_token: Discord access token
        
    Returns:
        dict: User information containing id, username, discriminator, etc.
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    
    response = requests.get('https://discord.com/api/v10/users/@me', headers=headers, timeout=10)
    
    if response.status_code != 200:
        logger.error(f'Discord user info fetch failed: {response.status_code} - {response.text}')
        raise ValueError(f'Discord user info fetch failed: {response.status_code}')
    
    return response.json()


def get_discord_guild_member(access_token, guild_id, user_id):
    """
    Check if user is a member of a Discord guild (server).
    
    Args:
        access_token: Discord access token
        guild_id: Discord guild (server) ID
        user_id: Discord user ID
        
    Returns:
        dict or None: Guild member information if user is a member, None otherwise
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    
    response = requests.get(
        f'https://discord.com/api/v10/guilds/{guild_id}/members/{user_id}',
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        return None  # User is not a member
    else:
        logger.error(f'Discord guild member check failed: {response.status_code} - {response.text}')
        return None


def get_valid_discord_access_token(user):
    """
    Get valid Discord access token for user, refreshing if necessary.
    
    Args:
        user: User instance
        
    Returns:
        str or None: Valid access token, or None if not available or refresh failed
    """
    try:
        meta = user.meta
    except UserMeta.DoesNotExist:
        logger.debug(f'UserMeta does not exist for user {user.id}')
        return None
    
    logger.info(f'get_valid_discord_access_token: User {user.id} - has_access_token={bool(meta.discord_access_token)}, expires_at={meta.discord_token_expires_at}')
    
    if not meta.discord_access_token:
        logger.warning(f'No Discord access token for user {user.id}')
        return None
    
    # Check if token is expired
    if meta.discord_token_expires_at and meta.discord_token_expires_at <= timezone.now():
        # Token expired, try to refresh
        if not meta.discord_refresh_token:
            logger.warning(f'Discord token expired for user {user.id}, but no refresh token available')
            return None
        
        try:
            token_data = refresh_discord_token(meta.discord_refresh_token)
            
            # Update tokens
            meta.discord_access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                meta.discord_refresh_token = token_data['refresh_token']
            
            expires_in = token_data.get('expires_in', 3600)
            meta.discord_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            meta.save(update_fields=['discord_access_token', 'discord_refresh_token', 'discord_token_expires_at'])
            
            logger.info(f'Discord token refreshed for user {user.id}')
            return meta.discord_access_token
        except Exception as e:
            logger.error(f'Failed to refresh Discord token for user {user.id}: {str(e)}')
            # Clear invalid tokens
            meta.discord_access_token = None
            meta.discord_refresh_token = None
            meta.discord_token_expires_at = None
            meta.save(update_fields=['discord_access_token', 'discord_refresh_token', 'discord_token_expires_at'])
            return None
    
    return meta.discord_access_token

