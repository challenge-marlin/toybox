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
    """Share to Discord."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        asset_id = request.data.get('assetId')
        if not asset_id:
            return Response({'ok': False, 'error': 'assetId required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Discord bot configuration
        bot_token = settings.DISCORD_BOT_TOKEN
        channel_id = settings.DISCORD_CHANNEL_ID
        
        if not bot_token or not channel_id:
            return Response({'ok': False, 'error': 'Discord not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get submission by ID
            try:
                submission = Submission.objects.get(id=asset_id, user=request.user)
            except Submission.DoesNotExist:
                return Response({'ok': False, 'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Determine asset type and URL
            asset_url = None
            asset_type = None
            
            if submission.game_url:
                asset_url = submission.game_url
                asset_type = 'game'
            elif submission.video_url:
                asset_url = submission.video_url
                asset_type = 'video'
            elif submission.image_url or submission.display_image_url:
                asset_url = submission.image_url or submission.display_image_url
                asset_type = 'image'
            else:
                return Response({'ok': False, 'error': 'No asset URL found'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Build Discord message
            try:
                meta = request.user.meta
                user_display_name = meta.display_name or meta.bio or request.user.display_id
            except:
                user_display_name = request.user.display_id
            message_content = f"**{user_display_name}** が投稿しました"
            
            # Prepare Discord API request
            discord_api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {bot_token}',
                'Content-Type': 'application/json'
            }
            
            # For images and videos, use embed with image/video
            if asset_type in ['image', 'video']:
                payload = {
                    'content': message_content,
                    'embeds': [{
                        'image' if asset_type == 'image' else 'video': {'url': asset_url},
                        'author': {
                            'name': user_display_name
                        },
                        'timestamp': submission.created_at.isoformat()
                    }]
                }
            else:
                # For games, just send a link
                payload = {
                    'content': f"{message_content}\n{asset_url}"
                }
            
            # Send to Discord
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
                logger.error(f'Discord API error: {response.status_code} - {error_text}')
                
                # Check for file size limit (25MB for Discord)
                if 'file size' in error_text.lower() or 'too large' in error_text.lower():
                    return Response({
                        'ok': False,
                        'error': 'ファイルサイズが大きすぎます（25MB以下）'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({
                    'ok': False,
                    'error': f'Discord API error: {response.status_code}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Discord API request failed: {str(e)}')
            return Response({
                'ok': False,
                'error': f'Discord API request failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f'Discord share error: {str(e)}')
            return Response({
                'ok': False,
                'error': f'Internal error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

