"""
Sharing views.
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.utils import timezone
from submissions.models import Submission
from .models import DiscordShare
import requests
import logging

logger = logging.getLogger(__name__)


class DiscordShareView(views.APIView):
    """Share to Discord using bot token."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        asset_id = request.data.get('assetId')
        if not asset_id:
            return Response({'ok': False, 'error': 'assetId required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get bot token and channel ID from settings
        bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', '')
        channel_id = getattr(settings, 'DISCORD_CHANNEL_ID', '')
        
        if not bot_token or not channel_id:
            logger.warning('Discord not configured: DISCORD_BOT_TOKEN or DISCORD_CHANNEL_ID is missing')
            return Response({
                'ok': False, 
                'error': 'Discord機能が設定されていません。管理者にお問い合わせください。'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # Get submission by ID (allow sharing others' work)
            try:
                submission = Submission.objects.get(id=asset_id, deleted_at__isnull=True)
            except Submission.DoesNotExist:
                return Response({'ok': False, 'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Determine asset type and get file data
            asset_file = None
            asset_filename = None
            asset_type = None
            
            if submission.game_url:
                # Games: just send URL
                asset_url = submission.game_url
                asset_type = 'game'
            elif submission.video_url:
                # Videos: download and upload as file
                try:
                    # Check file size first (Discord limit is 25MB for videos)
                    head_response = requests.head(submission.video_url, timeout=10, allow_redirects=True)
                    content_length = head_response.headers.get('content-length')
                    if content_length and int(content_length) > 25 * 1024 * 1024:
                        return Response({'ok': False, 'error': '動画ファイルが大きすぎます（25MB以下）'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Download video content
                    video_response = requests.get(submission.video_url, timeout=60)
                    if video_response.status_code == 200:
                        # Check actual downloaded size
                        if len(video_response.content) > 25 * 1024 * 1024:
                            return Response({'ok': False, 'error': '動画ファイルが大きすぎます（25MB以下）'}, status=status.HTTP_400_BAD_REQUEST)
                        
                        asset_file = video_response.content
                        # Determine filename from URL or content-type
                        import os
                        from urllib.parse import urlparse
                        parsed_url = urlparse(submission.video_url)
                        asset_filename = os.path.basename(parsed_url.path) or 'video.mp4'
                        if not asset_filename.endswith(('.mp4', '.webm', '.ogg', '.mov')):
                            # Use content-type to determine extension
                            content_type = video_response.headers.get('content-type', 'video/mp4')
                            ext_map = {
                                'video/mp4': '.mp4',
                                'video/webm': '.webm',
                                'video/ogg': '.ogg',
                                'video/quicktime': '.mov'
                            }
                            ext = ext_map.get(content_type, '.mp4')
                            asset_filename = f'video{ext}'
                        asset_type = 'video'
                        logger.info(f'Discord share: downloaded video from URL, filename={asset_filename}, size={len(asset_file)} bytes')
                    else:
                        logger.error(f'Failed to download video: {video_response.status_code}')
                        return Response({'ok': False, 'error': 'Failed to download video'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    logger.error(f'Failed to download video from URL: {str(e)}', exc_info=True)
                    return Response({'ok': False, 'error': f'Failed to download video: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif submission.image:
                # Prefer image field: read file directly
                try:
                    asset_file = submission.image.open('rb')
                    asset_filename = submission.image.name.split('/')[-1] or 'image.png'
                    asset_type = 'image'
                    logger.info(f'Discord share: using image field, filename={asset_filename}')
                except Exception as e:
                    logger.error(f'Failed to open image file: {str(e)}')
                    return Response({'ok': False, 'error': 'Failed to read image file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif submission.image_url:
                # Download image from URL
                try:
                    img_response = requests.get(submission.image_url, timeout=10)
                    if img_response.status_code == 200:
                        # Determine filename from URL or content-type
                        import os
                        from urllib.parse import urlparse
                        parsed_url = urlparse(submission.image_url)
                        asset_filename = os.path.basename(parsed_url.path) or 'image.png'
                        if not asset_filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                            # Use content-type to determine extension
                            content_type = img_response.headers.get('content-type', 'image/png')
                            ext_map = {
                                'image/jpeg': '.jpg',
                                'image/jpg': '.jpg',
                                'image/png': '.png',
                                'image/gif': '.gif',
                                'image/webp': '.webp'
                            }
                            ext = ext_map.get(content_type, '.png')
                            asset_filename = f'image{ext}'
                        asset_file = img_response.content
                        asset_type = 'image'
                        logger.info(f'Discord share: downloaded image from URL, filename={asset_filename}')
                    else:
                        logger.error(f'Failed to download image: {img_response.status_code}')
                        return Response({'ok': False, 'error': 'Failed to download image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    logger.error(f'Failed to download image from URL: {str(e)}')
                    return Response({'ok': False, 'error': f'Failed to download image: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({'ok': False, 'error': 'No asset found'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get display names for both users
            try:
                sharer_meta = request.user.meta
                sharer_display_name = sharer_meta.display_name or sharer_meta.bio or request.user.display_id
            except:
                sharer_display_name = request.user.display_id
            
            try:
                author_meta = submission.author.meta
                author_display_name = author_meta.display_name or author_meta.bio or submission.author.display_id
            except:
                author_display_name = submission.author.display_id
            
            # Determine if sharing own work or someone else's
            is_own_work = request.user.id == submission.author.id
            
            # Build message content
            if is_own_work:
                message_content = f"**{sharer_display_name}**さんが自分の作品を投稿しました。"
            else:
                message_content = f"**{sharer_display_name}**さんが**{author_display_name}**さんの作品をシェアしました。"
            
            # Prepare Discord API request using bot token
            discord_api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {bot_token}'
            }
            
            # For images: upload file directly
            if asset_type == 'image' and asset_file:
                embed_author_name = sharer_display_name if is_own_work else f"{sharer_display_name} (シェア: {author_display_name})"
                
                # Prepare multipart/form-data payload
                import json
                payload_data = {
                    'content': message_content,
                    'embeds': [{
                        'author': {
                            'name': embed_author_name
                        },
                        'timestamp': submission.created_at.isoformat()
                    }]
                }
                
                # Send as multipart/form-data with file
                files = {
                    'file': (asset_filename, asset_file, 'image/png' if asset_filename.endswith('.png') else 'image/jpeg')
                }
                data = {
                    'payload_json': json.dumps(payload_data)
                }
                
                response = requests.post(discord_api_url, headers=headers, files=files, data=data, timeout=30)
                
                # Close file if it's a file object
                if hasattr(asset_file, 'close'):
                    asset_file.close()
            elif asset_type == 'video' and asset_file:
                # Videos: upload file directly (same as images)
                embed_author_name = sharer_display_name if is_own_work else f"{sharer_display_name} (シェア: {author_display_name})"
                
                # Prepare multipart/form-data payload
                import json
                payload_data = {
                    'content': message_content,
                    'embeds': [{
                        'author': {
                            'name': embed_author_name
                        },
                        'timestamp': submission.created_at.isoformat()
                    }]
                }
                
                # Determine video content type
                video_content_type = 'video/mp4'
                if asset_filename.endswith('.webm'):
                    video_content_type = 'video/webm'
                elif asset_filename.endswith('.ogg'):
                    video_content_type = 'video/ogg'
                elif asset_filename.endswith('.mov'):
                    video_content_type = 'video/quicktime'
                
                # Send as multipart/form-data with file
                files = {
                    'file': (asset_filename, asset_file, video_content_type)
                }
                data = {
                    'payload_json': json.dumps(payload_data)
                }
                
                response = requests.post(discord_api_url, headers=headers, files=files, data=data, timeout=60)
            else:
                # For games, send with button component
                embed_author_name = sharer_display_name if is_own_work else f"{sharer_display_name} (シェア: {author_display_name})"
                payload = {
                    'content': message_content,
                    'embeds': [{
                        'title': 'ゲーム作品',
                        'description': f'ゲームをプレイするには、下のボタンをクリックしてください。',
                        'author': {
                            'name': embed_author_name
                        },
                        'timestamp': submission.created_at.isoformat(),
                        'color': 0x5865F2  # Discord blue color
                    }],
                    'components': [{
                        'type': 1,  # ActionRow
                        'components': [{
                            'type': 2,  # Button
                            'style': 5,  # Link button
                            'label': 'ゲームを開く',
                            'url': asset_url
                        }]
                    }]
                }
                headers['Content-Type'] = 'application/json'
                response = requests.post(discord_api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                message_data = response.json()
                message_id = message_data.get('id')
                
                # Save share record
                DiscordShare.objects.create(
                    user=request.user,
                    submission=submission,
                    share_channel=channel_id,
                    message_id=message_id
                )
                
                logger.info(f'Discord share successful: user={request.user.id}, submission={asset_id}, message_id={message_id}')
                
                return Response({
                    'ok': True,
                    'discordMessageId': message_id
                })
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_message = error_json.get('message', error_text)
                    error_code = error_json.get('code', response.status_code)
                except:
                    error_message = error_text
                    error_code = response.status_code
                
                logger.error(f'Discord API error: {response.status_code} - {error_message} (code: {error_code})')
                
                # Handle specific error codes
                if response.status_code == 401:
                    return Response({
                        'ok': False,
                        'error': 'Discord認証エラー: Botトークンが無効です。管理者にお問い合わせください。'
                    }, status=status.HTTP_401_UNAUTHORIZED)
                elif response.status_code == 403:
                    return Response({
                        'ok': False,
                        'error': 'Discord権限エラー: Botにチャンネルへの投稿権限がありません。管理者にお問い合わせください。'
                    }, status=status.HTTP_403_FORBIDDEN)
                elif response.status_code == 404:
                    return Response({
                        'ok': False,
                        'error': 'Discordチャンネルが見つかりません: Channel IDを確認してください'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                # Check for file size limit (25MB for Discord)
                if 'file size' in error_message.lower() or 'too large' in error_message.lower():
                    return Response({
                        'ok': False,
                        'error': 'ファイルサイズが大きすぎます（25MB以下）'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'ok': False,
                    'error': f'Discord API error ({response.status_code}): {error_message}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Discord API request failed: {str(e)}')
            return Response({
                'ok': False,
                'error': f'Discord API request failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f'Discord share error: {str(e)}', exc_info=True)
            import traceback
            logger.error(f'Traceback: {traceback.format_exc()}')
            return Response({
                'ok': False,
                'error': f'Internal error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DiscordStatusView(views.APIView):
    """Check Discord bot configuration status."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get Discord bot configuration status."""
        bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', '')
        channel_id = getattr(settings, 'DISCORD_CHANNEL_ID', '')
        
        # Bot is always "connected" if configured
        discord_configured = bool(bot_token and channel_id)
        
        return Response({
            'ok': True,
            'discord_connected': discord_configured,
            'guild_member': discord_configured,  # Always true if bot is configured
            'discord_username': None,  # Not applicable for bot
        })

