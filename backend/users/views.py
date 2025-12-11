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
        if display_name:
            meta.display_name = display_name
        if bio is not None:
            meta.bio = bio
        
        meta.save()
        
        logger.info(f'Updated profile for user {request.user.display_id}: display_name={display_name}, bio length={len(bio)}')
        
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
        
        # Verify file was saved
        full_path = default_storage.path(filepath)
        if not os.path.exists(full_path):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'File was not saved correctly: {full_path}')
            return Response({'error': 'ファイルの保存に失敗しました'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Build URL using MEDIA_URL setting to ensure consistency
        # Use /uploads/profiles/ path directly
        relative_url = f'/uploads/profiles/{filename}'
        
        # Build absolute URL
        if hasattr(request, 'build_absolute_uri'):
            file_url = request.build_absolute_uri(relative_url)
        else:
            # Fallback: construct URL manually
            file_url = f"{request.scheme}://{request.get_host()}{relative_url}"
        
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
        
        # アバターURLとヘッダーURLの取得と検証（統一ユーティリティを使用）
        from toybox.image_utils import get_image_url, verify_image_file_exists
        
        # アバターURL
        avatar_url = None
        if user.avatar_url:
            if verify_image_file_exists(user.avatar_url):
                avatar_url = get_image_url(
                    image_url_field=user.avatar_url,
                    request=request,
                    verify_exists=False  # 既に検証済み
                )
            else:
                # ファイルが存在しない場合はデータベースをクリア
                user.avatar_url = None
                user.save(update_fields=['avatar_url'])
        
        # ヘッダーURL
        header_url = None
        if meta.header_url:
            if verify_image_file_exists(meta.header_url):
                header_url = get_image_url(
                    image_url_field=meta.header_url,
                    request=request,
                    verify_exists=False  # 既に検証済み
                )
            else:
                # ファイルが存在しない場合はデータベースをクリア
                meta.header_url = None
                meta.save(update_fields=['header_url'])
        
        # 称号のバナー画像URLを取得
        active_title_image_url = None
        if active_title:
            try:
                from gamification.models import Title
                title_obj = Title.objects.filter(name=active_title).first()
                if title_obj:
                    active_title_image_url = get_image_url(
                        image_field=title_obj.image,
                        image_url_field=title_obj.image_url,
                        request=request,
                        verify_exists=True
                    )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to get title image for {active_title}: {e}')
        
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
            'avatarUrl': avatar_url,
            'headerUrl': header_url,
            'bio': meta.bio,
            'activeTitle': active_title,
            'activeTitleImageUrl': active_title_image_url,
            'activeTitleUntil': active_title_until.isoformat() if active_title_until else None,
            'updatedAt': meta.updated_at.isoformat() if meta.updated_at else None,
            'totalLikes': total_likes
        })


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
