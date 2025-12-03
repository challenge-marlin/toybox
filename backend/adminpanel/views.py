"""
Adminpanel app views for DRF - Admin API.
"""
from rest_framework import viewsets, status, filters, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from toybox.permissions import IsAdminOrAyatoriOrOffice, IsAdminOrAyatori, IsAdmin
from .models import AdminAuditLog
from users.models import User, UserMeta, UserCard, UserRegistration
from submissions.models import Submission
from sharing.models import DiscordShare
from .serializers import (
    AdminUserSerializer, AdminUserDetailSerializer,
    AdminSubmissionSerializer, AdminDiscordShareSerializer,
    AdminAuditLogSerializer
)
import requests
import json
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin user management viewset."""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrAyatoriOrOffice]
    serializer_class = AdminUserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email', 'display_id']
    filterset_fields = ['role', 'is_suspended']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'retrieve':
            return AdminUserDetailSerializer
        return AdminUserSerializer
    
    @action(detail=True, methods=['post'])
    def warn(self, request, pk=None):
        """Issue warning to user."""
        user = self.get_object()
        message = request.data.get('message', '')
        
        user.warning_count += 1
        if user.warning_notes:
            user.warning_notes += f'\n[{timezone.now().isoformat()}] {message}'
        else:
            user.warning_notes = f'[{timezone.now().isoformat()}] {message}'
        user.save()
        
        # Log audit
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.WARN,
            payload={'message': message, 'warning_count': user.warning_count}
        )
        
        return Response({'ok': True, 'warning_count': user.warning_count})
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend user."""
        user = self.get_object()
        user.is_suspended = True
        user.save()
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.SUSPEND,
            payload={}
        )
        
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'])
    def unsuspend(self, request, pk=None):
        """Unsuspend user."""
        user = self.get_object()
        user.is_suspended = False
        user.save()
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.UNSUSPEND,
            payload={}
        )
        
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'])
    def ban(self, request, pk=None):
        """Ban user."""
        user = self.get_object()
        user.banned_at = timezone.now()
        user.save()
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.BAN,
            payload={}
        )
        
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        """Unban user."""
        user = self.get_object()
        user.banned_at = None
        user.save()
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.UNBAN,
            payload={}
        )
        
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset user password."""
        user = self.get_object()
        import secrets
        temp_password = secrets.token_urlsafe(12)
        user.set_password(temp_password)
        user.save()
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.RESET_PASSWORD,
            payload={'temp_password': temp_password}  # In production, send via email
        )
        
        return Response({
            'ok': True,
            'temp_password': temp_password  # Remove in production
        })


class AdminSubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin submission management viewset."""
    queryset = Submission.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrAyatoriOrOffice]
    serializer_class = AdminSubmissionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['caption']
    filterset_fields = ['status', 'author']
    
    def get_queryset(self):
        """Filter submissions."""
        queryset = super().get_queryset()
        
        # Include deleted if requested
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(deleted_at__isnull=True)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        """Soft delete submission."""
        submission = self.get_object()
        reason = request.data.get('reason', '')
        
        submission.soft_delete(reason=reason)
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=submission.author,
            target_submission=submission,
            action=AdminAuditLog.Action.DELETE,
            payload={'reason': reason}
        )
        
        return Response({'ok': True})
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore soft-deleted submission."""
        submission = self.get_object()
        submission.restore()
        
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=submission.author,
            target_submission=submission,
            action=AdminAuditLog.Action.RESTORE,
            payload={}
        )
        
        return Response({'ok': True})


class AdminDiscordShareViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin Discord share viewset."""
    queryset = DiscordShare.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrAyatoriOrOffice]
    serializer_class = AdminDiscordShareSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'share_channel']
    ordering = ['-shared_at']


class AdminAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin audit log viewset."""
    queryset = AdminAuditLog.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrAyatori]
    serializer_class = AdminAuditLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['actor', 'target_user', 'target_submission', 'action']
    ordering = ['-created_at']


class DiscordBotPostView(views.APIView):
    """Discord bot post API endpoint for admin."""
    permission_classes = [IsAuthenticated, IsAdmin]
    
    def post(self, request):
        """Post message to Discord channel."""
        message = request.data.get('message', '').strip()
        file = request.FILES.get('file')
        
        if not message and not file:
            return Response({
                'ok': False,
                'error': 'メッセージまたはファイルのいずれかが必要です。'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get Discord configuration
        try:
            bot_token = getattr(settings, 'DISCORD_BOT_TOKEN', '')
            channel_id = getattr(settings, 'DISCORD_CHANNEL_ID', '')
        except Exception as e:
            logger.error(f'Failed to get Discord settings: {str(e)}', exc_info=True)
            return Response({
                'ok': False,
                'error': 'Discord設定の取得に失敗しました。'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not bot_token or not channel_id:
            return Response({
                'ok': False,
                'error': 'Discord機能が設定されていません。DISCORD_BOT_TOKENとDISCORD_CHANNEL_IDを設定してください。'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Validate file size if provided
        if file and file.size > 25 * 1024 * 1024:
            return Response({
                'ok': False,
                'error': 'ファイルサイズが25MBを超えています。'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            discord_api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
            headers = {
                'Authorization': f'Bot {bot_token}'
            }
            
            if file:
                # Upload file with message
                # Determine content type
                content_type = file.content_type
                if not content_type:
                    if file.name.endswith('.png'):
                        content_type = 'image/png'
                    elif file.name.endswith('.jpg') or file.name.endswith('.jpeg'):
                        content_type = 'image/jpeg'
                    elif file.name.endswith('.webp'):
                        content_type = 'image/webp'
                    elif file.name.endswith('.gif'):
                        content_type = 'image/gif'
                    elif file.name.endswith('.mp4'):
                        content_type = 'video/mp4'
                    elif file.name.endswith('.webm'):
                        content_type = 'video/webm'
                    elif file.name.endswith('.ogg'):
                        content_type = 'video/ogg'
                    else:
                        content_type = 'application/octet-stream'
                
                # Prepare multipart/form-data payload
                payload_data = {}
                if message:
                    payload_data['content'] = message
                
                files_data = {
                    'file': (file.name, file.read(), content_type)
                }
                data = {
                    'payload_json': json.dumps(payload_data)
                }
                
                response = requests.post(
                    discord_api_url,
                    headers=headers,
                    files=files_data,
                    data=data,
                    timeout=60
                )
            else:
                # Send text message only
                payload = {
                    'content': message
                }
                
                response = requests.post(
                    discord_api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
            
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                message_id = response_data.get('id')
                
                # Log audit
                AdminAuditLog.objects.create(
                    actor=request.user,
                    action=AdminAuditLog.Action.OTHER,
                    payload={
                        'action': 'discord_bot_post',
                        'message_id': message_id,
                        'has_file': bool(file),
                        'message_length': len(message) if message else 0
                    }
                )
                
                return Response({
                    'ok': True,
                    'message_id': message_id
                })
            else:
                error_text = response.text
                logger.error(f'Discord API error: {response.status_code} - {error_text}')
                return Response({
                    'ok': False,
                    'error': f'Discord APIエラー: {response.status_code}'
                }, status=status.HTTP_502_BAD_GATEWAY)
                
        except requests.exceptions.Timeout:
            logger.error('Discord API timeout')
            return Response({
                'ok': False,
                'error': 'Discord APIへのリクエストがタイムアウトしました。'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            logger.error(f'Discord bot post error: {str(e)}', exc_info=True)
            return Response({
                'ok': False,
                'error': f'投稿処理中にエラーが発生しました: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
