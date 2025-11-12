"""
Sharing views.
"""
from rest_framework import views, status
from rest_framework.response import Response
from django.conf import settings
import requests

class DiscordShareView(views.APIView):
    """Share to Discord."""
    
    def post(self, request):
        asset_id = request.data.get('assetId')
        if not asset_id:
            return Response({'ok': False, 'error': 'assetId required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Discord webhook implementation
        bot_token = settings.DISCORD_BOT_TOKEN
        channel_id = settings.DISCORD_CHANNEL_ID
        
        if not bot_token or not channel_id:
            return Response({'ok': False, 'error': 'Discord not configured'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # TODO: Implement Discord API call
        return Response({'ok': True, 'discordMessageId': '123456789'})

