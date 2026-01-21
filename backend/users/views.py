"""
Users app views for DRF.
"""
import json
import random
import os
import logging
from pathlib import Path
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.conf import settings
from .serializers import UserMetaSerializer, CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer
from .models import UserMeta, UserCard, UserRegistration
from django.contrib.auth import get_user_model
from .discord_oauth import (
    get_discord_oauth_url,
    exchange_discord_code,
    get_discord_user_info,
    get_discord_guild_member,
    get_valid_discord_access_token,
)
from django.shortcuts import redirect
from django.utils import timezone

logger = logging.getLogger(__name__)
from datetime import timedelta

User = get_user_model()


class LoginView(TokenObtainPairView):
    """Login endpoint."""
    serializer_class = CustomTokenObtainPairSerializer


class RefreshTokenView(TokenRefreshView):
    """Refresh token endpoint."""
    pass


@method_decorator(csrf_exempt, name='dispatch')
class LoginWithStudySphereTokenView(APIView):
    """Login with StudySphere token (login_code)."""
    permission_classes = []  # Allow unauthenticated access
    
    def post(self, request):
        """Login using StudySphere login_code token."""
        token = request.data.get('token', '').strip()
        
        if not token:
            return Response({
                'error': 'トークンが指定されていません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # デバッグログ: 入力されたトークンをログ出力（最初の20文字のみ）
            logger.info(f'StudySphere token login attempt: token_length={len(token)}, token_preview={token[:20]}...')
            
            # トークンを正規化（前後の空白を除去、改行を除去）
            normalized_token = token.strip().replace('\n', '').replace('\r', '')
            
            # studysphere_login_codeと一致するユーザーを検索
            # まず完全一致で検索
            user = User.objects.filter(studysphere_login_code=normalized_token).first()
            
            # 完全一致が見つからない場合、大文字小文字を無視して検索
            if not user:
                user = User.objects.filter(studysphere_login_code__iexact=normalized_token).first()
            
            # まだ見つからない場合、データベース内の値を正規化して比較
            if not user:
                # データベース内のすべてのstudysphere_login_codeを取得
                all_users_with_code = User.objects.exclude(studysphere_login_code__isnull=True).exclude(studysphere_login_code='')
                logger.info(f'Searching for token match. Total users with login_code: {all_users_with_code.count()}')
                
                # データベース内の値を正規化して比較
                for db_user in all_users_with_code:
                    db_code = db_user.studysphere_login_code
                    if db_code:
                        normalized_db_code = db_code.strip().replace('\n', '').replace('\r', '')
                        if normalized_db_code.lower() == normalized_token.lower():
                            user = db_user
                            logger.info(f'Found user with normalized match: user_id={user.id}, display_id={user.display_id}')
                            break
                
                if not user:
                    # デバッグ用: 最初の5件のlogin_codeをログ出力
                    sample_codes = list(all_users_with_code.values_list('id', 'display_id', 'studysphere_login_code')[:5])
                    logger.warning(f'StudySphere token login failed: token not found. Input token (normalized): "{normalized_token}", length: {len(normalized_token)}. Sample login_codes: {sample_codes}')
                    return Response({
                        'error': 'トークンが一致しません。トークンが正しいか、アカウントが連携されているか確認してください。'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # アカウントがアクティブかチェック
            if not user.is_active:
                logger.warning(f'StudySphere token login failed: user {user.id} is inactive')
                return Response({
                    'error': 'アカウントが無効です'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # アカウントが停止されているかチェック
            if user.is_suspended or user.banned_at:
                logger.warning(f'StudySphere token login failed: user {user.id} is suspended or banned')
                return Response({
                    'error': 'アカウントが停止されています'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # トークン発行
            refresh = RefreshToken.for_user(user)
            response_data = {
                'ok': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }
            
            # ペナルティメッセージがある場合は含める
            if user.penalty_message and user.penalty_type:
                response_data['penalty'] = {
                    'type': user.penalty_type,
                    'message': user.penalty_message,
                }
            
            logger.info(f'StudySphere token login successful for user {user.id} (display_id: {user.display_id})')
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f'Error in StudySphere token login: {str(e)}', exc_info=True)
            return Response({
                'error': 'ログイン処理中にエラーが発生しました'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            response_data = {
                'ok': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'role': user.role,  # ロール情報を追加
            }
            # ペナルティメッセージがある場合は含める
            if user.penalty_message and user.penalty_type:
                response_data['penalty'] = {
                    'type': user.penalty_type,
                    'message': user.penalty_message,
                }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response({
            'ok': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """Get current user information."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's information including role."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


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
        """Override list to return single user's meta (for GET /api/users/me/meta/)."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        # Check title expiration
        if meta.expires_at and meta.expires_at < timezone.now():
            meta.active_title = None
            meta.title_color = None
            meta.expires_at = None
            meta.save()
        
        serializer = self.get_serializer(meta)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch', 'put'], url_name='update')
    def update_meta(self, request):
        """Update current user's meta (for PATCH/PUT /api/users/me/meta/update_meta/)."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(meta, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """Override partial_update to update current user's meta (for PATCH /api/users/me/meta/{pk}/)."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        serializer = self.get_serializer(meta, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Override update to update current user's meta (for PUT /api/users/me/meta/{pk}/)."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        
        serializer = self.get_serializer(meta, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileUpdateView(APIView):
    """Update user profile (displayName and bio)."""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        """Update user profile."""
        import logging
        logger = logging.getLogger(__name__)
        
        display_name = request.data.get('displayName', '').strip()
        bio = request.data.get('bio', '').strip()
        
        # Get or create UserMeta
        meta, created = UserMeta.objects.get_or_create(user=request.user)
        
        # Update fields
        # display_nameは空文字列でも更新可能（削除を許可）
        if 'displayName' in request.data:
            meta.display_name = display_name
        if bio is not None:
            meta.bio = bio
        
        meta.save()
        
        logger.info(f'Updated profile for user {request.user.display_id}: display_name={display_name}, bio length={len(bio)}')
        
        serializer = UserMetaSerializer(meta)
        return Response(serializer.data)


class ProfileResetView(APIView):
    """Reset profile image to default (header or avatar)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Reset profile image to default."""
        reset_type = request.GET.get('type', 'avatar')  # 'avatar' or 'header'
        
        if reset_type == 'avatar':
            # アバターをデフォルトに戻す（Noneに設定）
            if request.user.avatar_url:
                # ファイルを削除（オプション）
                try:
                    from django.conf import settings
                    from pathlib import Path
                    if request.user.avatar_url.startswith('/uploads/profiles/'):
                        filename = request.user.avatar_url.split('/')[-1]
                        file_path = Path(settings.MEDIA_ROOT) / 'profiles' / filename
                        if file_path.exists():
                            file_path.unlink()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to delete avatar file: {e}')
            
            request.user.avatar_url = None
            request.user.save()
            return Response({'ok': True, 'message': 'アバターをデフォルトに戻しました', 'avatarUrl': None})
        else:  # header
            # ヘッダーをデフォルトに戻す（Noneに設定）
            meta, _ = UserMeta.objects.get_or_create(user=request.user)
            if meta.header_url:
                # ファイルを削除（オプション）
                try:
                    from django.conf import settings
                    from pathlib import Path
                    if meta.header_url.startswith('/uploads/profiles/'):
                        filename = meta.header_url.split('/')[-1]
                        file_path = Path(settings.MEDIA_ROOT) / 'profiles' / filename
                        if file_path.exists():
                            file_path.unlink()
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to delete header file: {e}')
            
            meta.header_url = None
            meta.save()
            return Response({'ok': True, 'message': 'ヘッダーをデフォルトに戻しました', 'headerUrl': None})


class ProfileUploadView(APIView):
    """Upload profile image (header or avatar)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Upload profile image or reset to default."""
        from django.core.files.storage import default_storage
        from django.conf import settings
        import os
        import uuid
        
        upload_type = request.GET.get('type', 'avatar')  # 'avatar' or 'header'
        action = request.data.get('action', 'upload')  # 'upload' or 'reset'
        
        # リセット処理
        if action == 'reset':
            if upload_type == 'avatar':
                # アバターをデフォルトに戻す（Noneに設定）
                if request.user.avatar_url:
                    # ファイルを削除（オプション）
                    try:
                        from pathlib import Path
                        if request.user.avatar_url.startswith('/uploads/profiles/'):
                            filename = request.user.avatar_url.split('/')[-1]
                            file_path = Path(settings.MEDIA_ROOT) / 'profiles' / filename
                            if file_path.exists():
                                file_path.unlink()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f'Failed to delete avatar file: {e}')
                
                request.user.avatar_url = None
                request.user.save()
                return Response({'ok': True, 'message': 'アバターをデフォルトに戻しました', 'avatarUrl': None})
            else:  # header
                # ヘッダーをデフォルトに戻す（Noneに設定）
                meta, _ = UserMeta.objects.get_or_create(user=request.user)
                if meta.header_url:
                    # ファイルを削除（オプション）
                    try:
                        from pathlib import Path
                        if meta.header_url.startswith('/uploads/profiles/'):
                            filename = meta.header_url.split('/')[-1]
                            file_path = Path(settings.MEDIA_ROOT) / 'profiles' / filename
                            if file_path.exists():
                                file_path.unlink()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f'Failed to delete header file: {e}')
                
                meta.header_url = None
                meta.save()
                return Response({'ok': True, 'message': 'ヘッダーをデフォルトに戻しました', 'headerUrl': None})
        
        # アップロード処理
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if file.content_type not in allowed_types:
            return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 画像をJPGに変換して最適化
        from toybox.image_optimizer import optimize_image_to_jpg
        optimized_image = optimize_image_to_jpg(
            file,
            max_width=1920 if upload_type == 'header' else 512,  # ヘッダーは1920px、アバターは512px
            max_height=1920 if upload_type == 'header' else 512,
            quality=85
        )
        
        if optimized_image:
            # 最適化された画像を保存
            filename = f'{upload_type}_{request.user.id}_{uuid.uuid4().hex[:8]}.jpg'
            from django.core.files.base import ContentFile
            filepath = default_storage.save(f'profiles/{filename}', ContentFile(optimized_image.read()))
        else:
            # 最適化に失敗した場合は元のファイルを保存
            file_ext = os.path.splitext(file.name)[1] or '.jpg'
            filename = f'{upload_type}_{request.user.id}_{uuid.uuid4().hex[:8]}{file_ext}'
            filepath = default_storage.save(f'profiles/{filename}', file)
        
        # Verify file was saved
        full_path = default_storage.path(filepath)
        if not os.path.exists(full_path):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'File was not saved correctly: {full_path}')
            return Response({'error': 'ファイルの保存に失敗しました'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # アバターの場合のみサムネイルを生成（ヘッダーはサムネイル不要）
        thumbnail_filename = None
        if upload_type == 'avatar':
            try:
                from toybox.image_optimizer import generate_thumbnail
                thumbnail_data = generate_thumbnail(full_path, max_size=300, quality=80)
                if thumbnail_data:
                    thumbnail_filename = f'{upload_type}_{request.user.id}_{uuid.uuid4().hex[:8]}_thumb.jpg'
                    thumbnail_filepath = default_storage.save(f'profiles/{thumbnail_filename}', ContentFile(thumbnail_data.read()))
                    logger.info(f'Generated thumbnail: {thumbnail_filepath}')
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to generate thumbnail: {e}')
        
        # Build URL using MEDIA_URL setting to ensure consistency
        # Use /uploads/profiles/ path directly
        relative_url = f'/uploads/profiles/{filename}'
        thumbnail_url = f'/uploads/profiles/{thumbnail_filename}' if thumbnail_filename else None
        
        # Build absolute URL
        if hasattr(request, 'build_absolute_uri'):
            file_url = request.build_absolute_uri(relative_url)
            if thumbnail_url:
                thumbnail_url = request.build_absolute_uri(thumbnail_url)
        else:
            # Fallback: construct URL manually
            file_url = f"{request.scheme}://{request.get_host()}{relative_url}"
            if thumbnail_url:
                thumbnail_url = f"{request.scheme}://{request.get_host()}{thumbnail_url}"
        
        # Update user or meta
        if upload_type == 'avatar':
            request.user.avatar_url = file_url
            request.user.save()
            return Response({
                'ok': True,
                'avatarUrl': request.user.avatar_url,
                'avatarThumbnailUrl': thumbnail_url
            })
        else:  # header
            meta, _ = UserMeta.objects.get_or_create(user=request.user)
            meta.header_url = file_url
            meta.save()
            return Response({
                'ok': True,
                'headerUrl': meta.header_url
            })
    
    def patch(self, request):
        """Reset profile image to default (header or avatar)."""
        reset_type = request.GET.get('type', 'avatar')  # 'avatar' or 'header'
        action = request.data.get('action', 'reset')  # 'reset' to set to default
        
        if action == 'reset':
            if reset_type == 'avatar':
                # アバターをデフォルトに戻す（Noneに設定）
                if request.user.avatar_url:
                    # ファイルを削除（オプション）
                    try:
                        from django.conf import settings
                        from pathlib import Path
                        if request.user.avatar_url.startswith('/uploads/profiles/'):
                            filename = request.user.avatar_url.split('/')[-1]
                            file_path = Path(settings.MEDIA_ROOT) / 'profiles' / filename
                            if file_path.exists():
                                file_path.unlink()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f'Failed to delete avatar file: {e}')
                
                request.user.avatar_url = None
                request.user.save()
                return Response({'ok': True, 'message': 'アバターをデフォルトに戻しました', 'avatarUrl': None})
            else:  # header
                # ヘッダーをデフォルトに戻す（Noneに設定）
                meta, _ = UserMeta.objects.get_or_create(user=request.user)
                if meta.header_url:
                    # ファイルを削除（オプション）
                    try:
                        from django.conf import settings
                        from pathlib import Path
                        if meta.header_url.startswith('/uploads/profiles/'):
                            filename = meta.header_url.split('/')[-1]
                            file_path = Path(settings.MEDIA_ROOT) / 'profiles' / filename
                            if file_path.exists():
                                file_path.unlink()
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f'Failed to delete header file: {e}')
                
                meta.header_url = None
                meta.save()
                return Response({'ok': True, 'message': 'ヘッダーをデフォルトに戻しました', 'headerUrl': None})
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Delete profile image (header or avatar) - alias for PATCH with reset action."""
        # DELETEメソッドもサポート（後方互換性のため）
        return self.patch(request)


class ProfileGetView(APIView):
    """Get public profile by anonId."""
    permission_classes = []  # Allow unauthenticated access
    
    def get(self, request, anon_id):
        """Get public profile."""
        try:
            # StudySphere経由のユーザーの場合、「StudySphereUser」が渡される可能性がある
            # その場合は認証済みユーザーのプロフィールを返す
            if anon_id == 'StudySphereUser' and request.user.is_authenticated:
                user = request.user
            else:
                # Find user by display_id or studysphere_login_code
                # StudySphereユーザーの場合はトークン（studysphere_login_code）で検索
                user = None
                try:
                    user = User.objects.get(display_id=anon_id)
                except User.DoesNotExist:
                    # display_idで見つからない場合、studysphere_login_codeで検索
                    try:
                        user = User.objects.get(studysphere_login_code=anon_id)
                    except User.DoesNotExist:
                        pass
            
            if not user:
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
        except Exception as e:
            logger.error(f'[ProfileGetView] Error finding user {anon_id}: {e}', exc_info=True)
            return Response({
                'error': 'プロフィールの取得に失敗しました',
                'anonId': anon_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f'[ProfileGetView] Error finding user {anon_id}: {e}', exc_info=True)
            return Response({
                'error': 'プロフィールの取得に失敗しました',
                'anonId': anon_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get or create UserMeta
            meta, _ = UserMeta.objects.get_or_create(user=user)
            
            # Check title expiration
            active_title = meta.active_title
            active_title_until = meta.expires_at
            if active_title and active_title_until:
                if active_title_until <= timezone.now():
                    # Title expired, clear it in database
                    meta.active_title = None
                    meta.title_color = None
                    meta.expires_at = None
                    meta.save(update_fields=['active_title', 'title_color', 'expires_at'])
                    active_title = None
                    active_title_until = None
            
            # Log title data for debugging (especially for StudySphere users)
            profile_logger = logging.getLogger(__name__)
            profile_logger.info(f'[ProfileGetView] User {user.id} (StudySphere: {bool(user.studysphere_user_id or user.studysphere_login_code)}) - active_title: {active_title}, expires_at: {active_title_until}')
            
            # Get display_name from display_name field, fallback to bio, then display_id
            # StudySphere経由のユーザーの場合、display_idの代わりに'StudySphereUser'を使用
            fallback_id = 'StudySphereUser' if (user.studysphere_user_id or user.studysphere_login_code) else user.display_id
            display_name = meta.display_name or meta.bio or fallback_id
            
            # anonIdもStudySphere経由のユーザーの場合は'StudySphereUser'に変更
            anon_id = 'StudySphereUser' if (user.studysphere_user_id or user.studysphere_login_code) else user.display_id
            
            # アバターURLの取得（絶対URLに変換）
            avatar_url = None
            avatar_thumbnail_url = None
            try:
                from toybox.image_utils import get_image_url
                from toybox.image_optimizer import get_thumbnail_url
                profile_logger = logging.getLogger(__name__)
                avatar_url_raw = user.avatar_url
                profile_logger.info(f'[Profile Image Debug] ProfileGetView - User {user.id} avatar_url from DB: {avatar_url_raw}')
                if avatar_url_raw:
                    avatar_url = get_image_url(
                        image_url_field=avatar_url_raw,
                        request=request,
                        verify_exists=False  # 存在確認を行わない
                    )
                    profile_logger.info(f'[Profile Image Debug] ProfileGetView - User {user.id} avatar_url after get_image_url: {avatar_url}')
                    
                    # サムネイルURLを取得
                    if avatar_url:
                        avatar_thumbnail_url = get_thumbnail_url(avatar_url, max_size=300, quality=80)
                        if avatar_thumbnail_url == avatar_url:
                            avatar_thumbnail_url = None
            except Exception as e:
                profile_logger = logging.getLogger(__name__)
                profile_logger.error(f'[Profile Image Debug] ProfileGetView - Error getting avatar_url for user {user.id}: {e}', exc_info=True)
                avatar_url = None
                avatar_thumbnail_url = None
            
            # ヘッダーURLの取得（絶対URLに変換、サムネイルは生成しない）
            header_url = None
            try:
                from toybox.image_utils import get_image_url
                profile_logger = logging.getLogger(__name__)
                header_url_raw = meta.header_url
                profile_logger.info(f'[Profile Image Debug] ProfileGetView - User {user.id} header_url from DB: {header_url_raw}')
                if header_url_raw:
                    header_url = get_image_url(
                        image_url_field=header_url_raw,
                        request=request,
                        verify_exists=False  # 存在確認を行わない
                    )
                    profile_logger.info(f'[Profile Image Debug] ProfileGetView - User {user.id} header_url after get_image_url: {header_url}')
            except Exception as e:
                profile_logger = logging.getLogger(__name__)
                profile_logger.error(f'[Profile Image Debug] ProfileGetView - Error getting header_url for user {user.id}: {e}', exc_info=True)
                header_url = None
            
            # 称号のバナー画像URLを取得
            active_title_image_url = None
            if active_title:
                try:
                    from gamification.models import Title
                    from toybox.image_utils import get_image_url
                    title_obj = Title.objects.filter(name=active_title).first()
                    if title_obj:
                        active_title_image_url = get_image_url(
                            image_field=title_obj.image,
                            image_url_field=title_obj.image_url,
                            request=request,
                            verify_exists=False  # ファイルが存在しなくてもURLを返す
                        )
                        profile_logger.info(f'[ProfileGetView] User {user.id} - Found title object for "{active_title}", image_url: {active_title_image_url}')
                    else:
                        profile_logger.warning(f'[ProfileGetView] User {user.id} - Title object not found for "{active_title}"')
                except Exception as e:
                    profile_logger = logging.getLogger(__name__)
                    profile_logger.warning(f'Failed to get title image for {active_title}: {e}', exc_info=True)
            
            # 獲得したいいねの合計を計算
            total_likes = 0
            try:
                from submissions.models import Reaction
                total_likes = Reaction.objects.filter(
                    submission__author=user,
                    submission__deleted_at__isnull=True,
                    type=Reaction.Type.SUBMIT_MEDAL
                ).count()
            except Exception as e:
                profile_logger = logging.getLogger(__name__)
                profile_logger.warning(f'Failed to get total_likes for user {user.id}: {e}')
            
            response_data = {
                'anonId': anon_id,
                'displayName': display_name,
                'avatarUrl': avatar_url,
                'avatarThumbnailUrl': avatar_thumbnail_url,
                'headerUrl': header_url,
                'bio': meta.bio,
                'activeTitle': active_title,
                'activeTitleImageUrl': active_title_image_url,
                'activeTitleUntil': active_title_until.isoformat() if active_title_until else None,
                'updatedAt': meta.updated_at.isoformat() if meta.updated_at else None,
                'totalLikes': total_likes
            }
            
            # Log response data for debugging (especially for StudySphere users)
            profile_logger.info(f'[ProfileGetView] User {user.id} (StudySphere: {bool(user.studysphere_user_id or user.studysphere_login_code)}) - Response activeTitle: {response_data["activeTitle"]}, activeTitleImageUrl: {response_data["activeTitleImageUrl"]}')
            
            return Response(response_data)
        except Exception as e:
            profile_logger = logging.getLogger(__name__)
            profile_logger.error(f'[ProfileGetView] Error processing profile for user {user.id}: {e}', exc_info=True)
            import traceback
            error_traceback = traceback.format_exc()
            profile_logger.error(f'[ProfileGetView] Traceback: {error_traceback}')
            return Response({
                'error': 'プロフィールの取得に失敗しました',
                'anonId': user.display_id if user else anon_id,
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationListView(APIView):
    """List notifications for current user."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get notifications."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        notifications = meta.notifications or []
        
        # 未読の通知数を計算
        unread_count = sum(1 for n in notifications if not n.get('read', False))
        
        # フロントエンドとの互換性のため、items と unread も返す
        return Response({
            'items': notifications,
            'notifications': notifications,  # 後方互換性
            'unread': unread_count,
            'unreadCount': unread_count,  # 後方互換性
            'nextOffset': None  # 将来のページネーション用
        })


class NotificationReadView(APIView):
    """Mark notifications as read."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark notifications as read."""
        meta, _ = UserMeta.objects.get_or_create(user=request.user)
        notifications = meta.notifications or []
        
        # すべての通知を既読にする
        for notification in notifications:
            notification['read'] = True
        
        meta.notifications = notifications
        meta.save()
        
        return Response({'ok': True})


class TopicGenerateView(APIView):
    """Generate topic (work or game)."""
    permission_classes = [AllowAny]
    
    def _load_games_ideas(self):
        """Load games_idea.json file."""
        try:
            # BASE_DIR is backend/ directory
            # games_idea.json is in backend/data/games_idea.json
            json_path = Path(settings.BASE_DIR) / 'data' / 'games_idea.json'
            
            if not json_path.exists():
                # Try alternative path (if BASE_DIR is project root)
                json_path = Path(settings.BASE_DIR) / 'backend' / 'data' / 'games_idea.json'
            
            if not json_path.exists():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'games_idea.json not found. Tried: {json_path}')
                return []
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # File should now contain a single array
                if isinstance(data, list):
                    return data
                # If it's not a list, return empty
                return []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to load games_idea.json: {str(e)}')
            return []
    
    def _load_tricycle_media_ideas(self):
        """Load tricycle_media_ideas.json file."""
        try:
            # BASE_DIR is backend/ directory
            # tricycle_media_ideas.json is in backend/data/tricycle_media_ideas.json
            json_path = Path(settings.BASE_DIR) / 'data' / 'tricycle_media_ideas.json'
            
            if not json_path.exists():
                # Try alternative path (if BASE_DIR is project root)
                json_path = Path(settings.BASE_DIR) / 'backend' / 'data' / 'tricycle_media_ideas.json'
            
            if not json_path.exists():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'tricycle_media_ideas.json not found. Tried: {json_path}')
                return []
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # File should now contain a single array
                if isinstance(data, list):
                    return data
                # If it's not a list, return empty
                return []
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to load tricycle_media_ideas.json: {str(e)}')
            return []
    
    def _weighted_random_choice(self, games):
        """Select a game based on difficulty (lower difficulty = higher weight)."""
        if not games:
            return None
        
        # Calculate weights: lower difficulty = higher weight
        # difficulty 1-2: weight 5, 3-4: weight 3, 5-6: weight 2, 7+: weight 1
        weights = []
        for game in games:
            difficulty = game.get('difficulty', 5)
            if difficulty <= 2:
                weight = 5
            elif difficulty <= 4:
                weight = 3
            elif difficulty <= 6:
                weight = 2
            else:
                weight = 1
            weights.append(weight)
        
        # Weighted random selection
        selected = random.choices(games, weights=weights, k=1)[0]
        return selected
    
    def get(self, request):
        """Generate topic."""
        topic_type = request.query_params.get('type', 'game')  # 'work' or 'game'
        
        if topic_type == 'game':
            # Load games from games_idea.json
            games = self._load_games_ideas()
            
            if not games:
                return Response({
                    'error': 'ゲームのお題データを読み込めませんでした。'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Select a game with weighted random
            selected_game = self._weighted_random_choice(games)
            
            if not selected_game:
                return Response({
                    'error': 'ゲームのお題を選択できませんでした。'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'type': 'game',
                'title': selected_game.get('title', ''),
                'shortIdea': selected_game.get('shortIdea', ''),
                'description': selected_game.get('description', ''),
                'difficulty': selected_game.get('difficulty', 0),
                'category': selected_game.get('category', ''),
            })
        else:
            # Work topics - Load from tricycle_media_ideas.json
            media_ideas = self._load_tricycle_media_ideas()
            
            if not media_ideas:
                return Response({
                    'error': '画像・動画のお題データを読み込めませんでした。'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Random selection
            selected_idea = random.choice(media_ideas)
            
            media_type = selected_idea.get('type', 'image')
            type_text = '動画' if media_type == 'video' else '画像'
            
            return Response({
                'type': 'work',
                'mediaType': media_type,
                'typeText': type_text,
                'title': selected_idea.get('title', ''),
                'shortIdea': selected_idea.get('shortIdea', ''),
            })


class DiscordOAuthLoginView(APIView):
    """Discord OAuth2 login initiation."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Redirect to Discord OAuth2 authorization page."""
        try:
            # Store user ID in session for callback to retrieve
            request.session['discord_oauth_user_id'] = request.user.id
            request.session.modified = True
            logger.info(f'DiscordOAuthLoginView: Stored user {request.user.id} in session, session_key={request.session.session_key}')
            
            # Also include user ID in state parameter as backup
            import base64
            import json
            state_data = {'user_id': request.user.id}
            state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()
            
            oauth_url = get_discord_oauth_url(request=request, state=state)
            logger.info(f'DiscordOAuthLoginView: Generated OAuth URL with state parameter')
            return redirect(oauth_url)
        except ValueError as e:
            logger.error(f'Discord OAuth URL generation failed: {str(e)}')
            return Response({
                'ok': False,
                'error': 'Discord認証が設定されていません。管理者にお問い合わせください。'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class DiscordOAuthCallbackView(APIView):
    """Discord OAuth2 callback handler."""
    permission_classes = [AllowAny]  # Allow unauthenticated for callback
    
    def get(self, request):
        """Handle Discord OAuth2 callback."""
        logger.info(f'DiscordOAuthCallbackView: Callback received - code={bool(request.GET.get("code"))}, error={request.GET.get("error")}, state={request.GET.get("state")}, session_keys={list(request.session.keys())}')
        
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state')
        
        if error:
            logger.error(f'Discord OAuth error: {error}')
            return redirect('/me/?discord_auth_error=1')
        
        if not code:
            logger.error('Discord OAuth callback missing code')
            return redirect('/me/?discord_auth_error=1')
        
        try:
            # Exchange code for tokens
            token_data = exchange_discord_code(code, request=request)
            access_token = token_data['access_token']
            refresh_token = token_data.get('refresh_token')
            expires_in = token_data.get('expires_in', 3600)
            
            # Get user info
            user_info = get_discord_user_info(access_token)
            discord_user_id = user_info['id']
            discord_username = f"{user_info.get('username', '')}#{user_info.get('discriminator', '0000')}"
            
            # Check if user is authenticated (via session or token)
            user = request.user if request.user.is_authenticated else None
            logger.info(f'DiscordOAuthCallbackView: request.user.is_authenticated={request.user.is_authenticated}, user={user.id if user else None}')
            
            # Try to get user ID from state parameter
            user_id = None
            if state:
                try:
                    import base64
                    import json
                    state_data = json.loads(base64.urlsafe_b64decode(state.encode()).decode())
                    user_id = state_data.get('user_id')
                    logger.info(f'DiscordOAuthCallbackView: Extracted user_id={user_id} from state parameter')
                except Exception as e:
                    logger.warning(f'DiscordOAuthCallbackView: Failed to decode state parameter: {str(e)}')
            
            # If not authenticated via request.user, try to get from session
            if not user:
                if not user_id:
                    user_id = request.session.get('discord_oauth_user_id')
                    logger.info(f'DiscordOAuthCallbackView: Checking session for user_id, found={user_id}')
                
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        logger.info(f'DiscordOAuthCallbackView: Retrieved user {user.id} from session/state')
                    except User.DoesNotExist:
                        logger.warning(f'DiscordOAuthCallbackView: User {user_id} does not exist')
                        user = None
            
            if not user:
                # Store tokens in session for later association
                request.session['discord_access_token'] = access_token
                request.session['discord_refresh_token'] = refresh_token
                request.session['discord_user_id'] = discord_user_id
                request.session['discord_username'] = discord_username
                request.session['discord_expires_in'] = expires_in
                logger.warning('DiscordOAuthCallbackView: No authenticated user found, storing tokens in session')
                return redirect('/login/?discord_connected=1')
            
            # Associate Discord account with authenticated user
            meta, created = UserMeta.objects.get_or_create(user=user)
            meta.discord_access_token = access_token
            if refresh_token:
                meta.discord_refresh_token = refresh_token
            meta.discord_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            meta.discord_user_id = discord_user_id
            meta.discord_username = discord_username
            meta.save(update_fields=[
                'discord_access_token',
                'discord_refresh_token',
                'discord_token_expires_at',
                'discord_user_id',
                'discord_username',
            ])
            
            # Verify token was saved
            meta.refresh_from_db()
            logger.info(f'DiscordOAuthCallbackView: After save - has_access_token={bool(meta.discord_access_token)}, has_refresh_token={bool(meta.discord_refresh_token)}, expires_at={meta.discord_token_expires_at}, discord_user_id={meta.discord_user_id}')
            
            if not meta.discord_access_token:
                logger.error(f'Discord token not saved for user {user.id}')
                return redirect('/me/?discord_auth_error=1')
            
            # Verify token can be retrieved
            test_token = get_valid_discord_access_token(user)
            logger.info(f'DiscordOAuthCallbackView: Token verification - can_retrieve={bool(test_token)}')
            
            logger.info(f'Discord account linked for user {user.id}, discord_user_id={discord_user_id}, token_expires_at={meta.discord_token_expires_at}')
            return redirect('/me/?discord_connected=1')
            
        except Exception as e:
            logger.error(f'Discord OAuth callback error: {str(e)}', exc_info=True)
            return redirect('/me/?discord_auth_error=1')


class DiscordStatusView(APIView):
    """Check Discord authentication and guild membership status."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get Discord authentication and guild membership status."""
        try:
            meta = request.user.meta
        except UserMeta.DoesNotExist:
            return Response({
                'ok': True,
                'discord_connected': False,
                'guild_member': False,
            })
        
        # Check if Discord is connected
        # Debug: Check token fields before calling get_valid_discord_access_token
        logger.info(f'DiscordStatusView: User {request.user.id} - has_access_token={bool(meta.discord_access_token)}, has_refresh_token={bool(meta.discord_refresh_token)}, expires_at={meta.discord_token_expires_at}, discord_user_id={meta.discord_user_id}')
        
        access_token = get_valid_discord_access_token(request.user)
        discord_connected = bool(access_token)
        
        logger.info(f'DiscordStatusView: User {request.user.id} - access_token={bool(access_token)}, discord_connected={discord_connected}')
        
        guild_member = False
        if discord_connected:
            # Check guild membership
            server_id = getattr(settings, 'DISCORD_SERVER_ID', '')
            if server_id and meta.discord_user_id:
                try:
                    member_info = get_discord_guild_member(
                        access_token,
                        server_id,
                        meta.discord_user_id
                    )
                    guild_member = member_info is not None
                except Exception as e:
                    logger.warning(f'Failed to check guild membership for user {request.user.id}: {str(e)}')
        
        return Response({
            'ok': True,
            'discord_connected': discord_connected,
            'guild_member': guild_member,
            'discord_username': meta.discord_username if discord_connected else None,
        })


class TermsAgreeView(APIView):
    """Agree to terms of service (for paid users, first time only)."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Record terms agreement."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # 課金ユーザー以外はエラー
        if request.user.role != User.Role.PAID_USER:
            return Response({
                'error': 'この機能は課金ユーザーのみ利用できます'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # UserMetaを取得または作成
        meta, created = UserMeta.objects.get_or_create(user=request.user)
        
        # 既に同意済みの場合はエラー
        if meta.terms_agreed_at:
            return Response({
                'error': '既に利用規約に同意済みです'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 同意日時を記録
        meta.terms_agreed_at = timezone.now()
        meta.save()
        
        logger.info(f'Terms agreed by user {request.user.id} at {meta.terms_agreed_at}')
        
        return Response({
            'ok': True,
            'message': '利用規約への同意を記録しました',
            'agreed_at': meta.terms_agreed_at.isoformat()
        })


class ProfileSetStudySphereTokenView(APIView):
    """Set StudySphere login code token directly."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Set StudySphere login code token directly."""
        token = request.data.get('token', '').strip()
        
        if not token:
            return Response({
                'error': 'トークンが指定されていません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 現在のユーザーのstudysphere_login_codeを更新
            user = request.user
            user.studysphere_login_code = token
            user.save(update_fields=['studysphere_login_code'])
            
            logger.info(f'StudySphere login code set for user {user.id}, login_code_length={len(token)}')
            
            return Response({
                'ok': True,
                'message': 'StudySphereトークンを保存しました'
            })
            
        except Exception as e:
            logger.error(f'Error setting StudySphere token for user {request.user.id}: {str(e)}', exc_info=True)
            return Response({
                'error': 'トークンの保存中にエラーが発生しました'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileLinkStudySphereView(APIView):
    """Link StudySphere account to existing TOYBOX account."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Link StudySphere account using ticket token."""
        ticket = request.data.get('ticket', '').strip()
        
        if not ticket:
            return Response({
                'error': 'トークンが指定されていません'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # チケットを検証（StudySphere側のSSO APIを呼び出し）
            from sso_integration.services import verify_ticket
            result = verify_ticket(ticket)
            
            if not result.get("valid"):
                error_msg = result.get("error") or "無効なチケットです"
                logger.warning(f'Invalid StudySphere ticket for user {request.user.id}: {error_msg}')
                return Response({
                    'error': '無効なトークンです'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            sso_data = result.get("data") or {}
            studysphere_user_id = sso_data.get("user_id")
            studysphere_login_code = sso_data.get("login_code") or sso_data.get("username") or ""
            
            if not studysphere_user_id:
                logger.warning(f'Missing user_id in SSO data for user {request.user.id}')
                return Response({
                    'error': 'StudySphereユーザーIDが取得できませんでした'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 既に別のアカウントに紐づいているかチェック
            existing_user = User.objects.filter(studysphere_user_id=studysphere_user_id).exclude(id=request.user.id).first()
            if existing_user:
                logger.warning(f'StudySphere user_id {studysphere_user_id} already linked to user {existing_user.id}')
                return Response({
                    'error': 'このStudySphereアカウントは既に別のTOYBOXアカウントに紐づいています'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 現在のユーザーにStudySphere情報を紐づけ
            user = request.user
            user.studysphere_user_id = studysphere_user_id
            if studysphere_login_code:
                user.studysphere_login_code = studysphere_login_code
            user.save(update_fields=['studysphere_user_id', 'studysphere_login_code'])
            
            logger.info(f'StudySphere account linked for user {user.id}, studysphere_user_id={studysphere_user_id}, login_code={studysphere_login_code}')
            
            return Response({
                'ok': True,
                'message': 'StudySphereアカウントを連携しました',
                'studysphere_user_id': studysphere_user_id,
                'studysphere_username': sso_data.get("username") or studysphere_login_code
            })
            
        except Exception as e:
            logger.error(f'Error linking StudySphere account for user {request.user.id}: {str(e)}', exc_info=True)
            return Response({
                'error': 'StudySphereアカウントの連携中にエラーが発生しました'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
