"""
Adminpanel app views for DRF - Admin API.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
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
