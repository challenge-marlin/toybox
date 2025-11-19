"""
Users app views for DRF.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import UserMeta
from .serializers import UserMetaSerializer, CustomTokenObtainPairSerializer, RegisterSerializer

User = get_user_model()


class LoginView(TokenObtainPairView):
    """Login endpoint - returns JWT tokens."""
    serializer_class = CustomTokenObtainPairSerializer


class RefreshTokenView(TokenRefreshView):
    """Refresh token endpoint."""
    pass


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """Registration endpoint."""
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request):
        """Register a new user."""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'ok': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response({
            'ok': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserMetaViewSet(viewsets.ModelViewSet):
    """UserMeta viewset."""
    serializer_class = UserMetaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return current user's meta."""
        return UserMeta.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's metadata."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        # Check title expiration
        if meta.expires_at and meta.expires_at < timezone.now():
            meta.active_title = None
            meta.title_color = None
            meta.expires_at = None
            meta.save()
        
        serializer = self.get_serializer(meta)
        return Response(serializer.data)
    
    def list(self, request):
        """Override list to return single user's meta (for /api/users/me/meta/)."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        # Check title expiration
        if meta.expires_at and meta.expires_at < timezone.now():
            meta.active_title = None
            meta.title_color = None
            meta.expires_at = None
            meta.save()
        
        serializer = self.get_serializer(meta)
        return Response(serializer.data)


class ProfileUpdateView(APIView):
    """Update user profile (displayName and bio)."""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """Update user profile."""
        import logging
        logger = logging.getLogger(__name__)
        
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        display_name = request.data.get('displayName')
        bio = request.data.get('bio')
        
        logger.info(f'Profile update request: user={request.user.id}, displayName={display_name}, bio={bio}')
        
        # Update display_name if provided
        if display_name is not None:
            meta.display_name = display_name.strip() if display_name else ''
            logger.info(f'Updated display_name to: {meta.display_name}')
        
        # Update bio if provided
        if bio is not None:
            meta.bio = bio.strip() if bio else ''
            logger.info(f'Updated bio to: {meta.bio}')
        
        meta.save()
        logger.info(f'Saved UserMeta: display_name={meta.display_name}, bio={meta.bio}')
        
        serializer = UserMetaSerializer(meta)
        return Response(serializer.data)


class ProfileUploadView(APIView):
    """Upload profile image (header or avatar)."""
    
    def post(self, request):
        """Upload profile image."""
        from django.core.files.storage import default_storage
        from django.conf import settings
        import os
        import uuid
        
        upload_type = request.GET.get('type', 'avatar')  # 'avatar' or 'header'
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save file
        file_ext = os.path.splitext(file.name)[1] or '.jpg'
        filename = f'{upload_type}_{request.user.id}_{uuid.uuid4().hex[:8]}{file_ext}'
        filepath = default_storage.save(f'profiles/{filename}', file)
        
        # Get absolute URL
        file_url = default_storage.url(filepath)
        # Build absolute URL if needed
        if not file_url.startswith('http'):
            from django.http import HttpRequest
            if hasattr(request, 'build_absolute_uri'):
                file_url = request.build_absolute_uri(file_url)
            else:
                # Fallback: construct URL manually
                file_url = f"{request.scheme}://{request.get_host()}{file_url}"
        
        # Update user or meta
        if upload_type == 'avatar':
            request.user.avatar_url = file_url
            request.user.save()
            return Response({'ok': True, 'avatarUrl': request.user.avatar_url})
        else:  # header
            meta, _ = UserMeta.objects.get_or_create(user=request.user)
            meta.header_url = file_url
            meta.save()
            return Response({'ok': True, 'headerUrl': meta.header_url})


class ProfileGetView(APIView):
    """Get public profile by anonId."""
    permission_classes = []  # Allow unauthenticated access
    
    def get(self, request, anon_id):
        """Get public profile."""
        try:
            # Find user by display_id (which is used as anonId)
            user = User.objects.get(display_id=anon_id)
        except User.DoesNotExist:
            # Return empty profile if user not found
            return Response({
                'anonId': anon_id,
                'displayName': None,
                'avatarUrl': None,
                'headerUrl': None,
                'bio': None,
                'activeTitle': None,
                'activeTitleUntil': None,
                'updatedAt': None
            })
        
        # Get or create UserMeta
        meta, _ = UserMeta.objects.get_or_create(user=user)
        
        # Check title expiration
        active_title = meta.active_title
        active_title_until = meta.expires_at
        if active_title and active_title_until:
            if active_title_until <= timezone.now():
                active_title = None
                active_title_until = None
        
        # Get display_name from display_name field, fallback to bio, then display_id
        display_name = meta.display_name or meta.bio or user.display_id
        
        # 獲得したいいねの合計を計算
        from submissions.models import Reaction
        total_likes = Reaction.objects.filter(
            submission__author=user,
            submission__deleted_at__isnull=True,
            type=Reaction.Type.SUBMIT_MEDAL
        ).count()
        
        return Response({
            'anonId': user.display_id,
            'displayName': display_name,
            'avatarUrl': user.avatar_url,
            'headerUrl': meta.header_url,
            'bio': meta.bio,
            'activeTitle': active_title,
            'activeTitleUntil': active_title_until.isoformat() if active_title_until else None,
            'updatedAt': meta.updated_at.isoformat() if meta.updated_at else None,
            'totalLikes': total_likes
        })


class NotificationListView(APIView):
    """Get user's notifications."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get notifications list."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        notifications = meta.notifications or []
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        limit = max(1, min(100, limit))
        offset = max(0, offset)
        
        items = notifications[offset:offset + limit]
        unread_count = sum(1 for n in notifications if not n.get('read', False))
        next_offset = offset + len(items) if offset + len(items) < len(notifications) else None
        
        return Response({
            'items': items,
            'unread': unread_count,
            'nextOffset': next_offset
        })


class NotificationReadView(APIView):
    """Mark notifications as read."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark notifications as read."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        notifications = meta.notifications or []
        
        # If no indexes provided, mark all as read
        indexes = request.data.get('indexes', [])
        if not indexes:
            # Mark all as read
            for notification in notifications:
                notification['read'] = True
        else:
            # Mark specific indexes as read
            for idx in indexes:
                if isinstance(idx, int) and 0 <= idx < len(notifications):
                    notifications[idx]['read'] = True
        
        meta.notifications = notifications
        meta.save()
        
        return Response({'ok': True})
