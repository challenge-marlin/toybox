"""
Users app views for DRF.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
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


class ProfileUpdateView(APIView):
    """Update user profile (displayName and bio)."""
    
    def patch(self, request):
        """Update user profile."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        display_name = request.data.get('displayName', '').strip()
        bio = request.data.get('bio', '').strip()
        
        # Update display_name (stored in bio field)
        # Note: According to UserMetaSerializer.get_display_name(), 
        # display_name comes from bio field, so we store display_name in bio
        if display_name:
            meta.bio = display_name
        
        # Note: bio parameter is currently not used as UserMeta only has one bio field
        # which is used for display_name. If we need separate bio field, we'd need to add it to the model.
        
        meta.save()
        
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
        
        # Update user or meta
        if upload_type == 'avatar':
            request.user.avatar_url = default_storage.url(filepath)
            request.user.save()
            return Response({'ok': True, 'avatarUrl': request.user.avatar_url})
        else:  # header
            meta, _ = UserMeta.objects.get_or_create(user=request.user)
            meta.header_url = default_storage.url(filepath)
            meta.save()
            return Response({'ok': True, 'headerUrl': meta.header_url})
