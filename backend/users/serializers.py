"""
Users app serializers for DRF.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import UserMeta, UserCard, UserRegistration

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that uses display_id (ID) instead of email or username."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username and email fields if they exist
        if 'username' in self.fields:
            del self.fields['username']
        if 'email' in self.fields:
            del self.fields['email']
        # Add display_id field (ID)
        self.fields['display_id'] = serializers.CharField()
    
    def validate(self, attrs):
        display_id = attrs.get('display_id')
        password = attrs.get('password')
        
        if not display_id or not password:
            raise serializers.ValidationError({
                'non_field_errors': ['Must include "display_id" and "password".']
            })
        
        try:
            user = User.objects.get(display_id=display_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'non_field_errors': ['Invalid ID or password.']
            })
        
        if not user.check_password(password):
            raise serializers.ValidationError({
                'non_field_errors': ['Invalid ID or password.']
            })
        
        # BANされたアカウントでも警告メッセージを表示するために一時的にログインを許可
        # （警告メッセージ表示後に自動的にログアウトされる）
        # ただし、is_activeがFalseでBANされていない場合は通常通り拒否
        if not user.is_active and not (user.banned_at or user.penalty_type == 'BAN'):
            raise serializers.ValidationError({
                'non_field_errors': ['User account is disabled.']
            })
        
        # Generate tokens directly
        refresh = RefreshToken.for_user(user)
        
        # 警告メッセージをレスポンスに含める
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'role': user.role,  # ロール情報を追加
        }
        
        # ペナルティメッセージがある場合は含める
        if user.penalty_message and user.penalty_type:
            response_data['penalty'] = {
                'type': user.penalty_type,
                'message': user.penalty_message,
            }
        
        return response_data


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""
    avatar_url = serializers.SerializerMethodField()
    avatar_thumbnail_url = serializers.SerializerMethodField()
    display_id = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'display_id', 'role', 'avatar_url', 'avatar_thumbnail_url', 'is_suspended', 'banned_at', 'warning_count', 'studysphere_user_id']
        read_only_fields = ['id', 'role', 'is_suspended', 'banned_at', 'warning_count', 'studysphere_user_id']
    
    def get_display_id(self, obj):
        """Get display_id, but return 'StudySphereUser' for StudySphere users."""
        # StudySphere経由のユーザーの場合、IDを非表示にする
        if obj.studysphere_user_id or obj.studysphere_login_code:
            return 'StudySphereUser'
        return obj.display_id
    
    def get_avatar_url(self, obj):
        """Get absolute URL for avatar."""
        from toybox.image_utils import get_image_url
        request = self.context.get('request')
        avatar_url_raw = obj.avatar_url if hasattr(obj, 'avatar_url') else None
        if avatar_url_raw:
            return get_image_url(
                image_url_field=avatar_url_raw,
                request=request,
                verify_exists=False
            )
        return None
    
    def get_avatar_thumbnail_url(self, obj):
        """Get thumbnail URL for avatar."""
        avatar_url = self.get_avatar_url(obj)
        if avatar_url:
            from toybox.image_optimizer import get_thumbnail_url
            thumbnail_url = get_thumbnail_url(avatar_url, max_size=300, quality=80)
            if thumbnail_url and thumbnail_url != avatar_url:
                return thumbnail_url
        return None


class UserMetaSerializer(serializers.ModelSerializer):
    """UserMeta serializer."""
    display_id = serializers.SerializerMethodField()
    url_id = serializers.SerializerMethodField()  # URL用のID（StudySphereユーザーの場合はトークン）
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.URLField(source='user.avatar_url', read_only=True)
    
    def get_display_id(self, obj):
        """Get display_id, but return 'StudySphereUser' for StudySphere users."""
        user = obj.user
        # StudySphere経由のユーザーの場合、IDを非表示にする
        if user.studysphere_user_id or user.studysphere_login_code:
            return 'StudySphereUser'
        return user.display_id
    
    def get_url_id(self, obj):
        """Get ID for URL (use studysphere_login_code for StudySphere users)."""
        user = obj.user
        # StudySphere経由のユーザーの場合、URLにはトークンを使用
        if user.studysphere_login_code:
            return user.studysphere_login_code
        return user.display_id
    
    def get_display_name(self, obj):
        """Get display name from display_name field, fallback to bio, then display_id."""
        user = obj.user
        # StudySphere経由のユーザーの場合、display_idの代わりに'StudySphereUser'を使用
        fallback_id = 'StudySphereUser' if (user.studysphere_user_id or user.studysphere_login_code) else user.display_id
        return obj.display_name or obj.bio or fallback_id
    
    def to_representation(self, instance):
        """Override to check title expiry and add title image URL."""
        data = super().to_representation(instance)
        
        # アバターURLとヘッダーURLの取得（存在確認は行わず、URLをそのまま返す）
        from toybox.image_utils import get_image_url
        from toybox.image_optimizer import get_thumbnail_url
        import logging
        logger = logging.getLogger(__name__)
        request = self.context.get('request')
        
        # ユーザーのアバターURL（Userモデルから取得）
        user = instance.user
        avatar_url_raw = getattr(user, 'avatar_url', None)
        logger.info(f'[Profile Image Debug] UserMetaSerializer - User {user.id} avatar_url from DB: {avatar_url_raw}')
        
        avatar_url = None
        avatar_thumbnail_url = None
        if avatar_url_raw:
            avatar_url = get_image_url(
                image_url_field=avatar_url_raw,
                request=request,
                verify_exists=False  # 存在確認を行わない
            )
            logger.info(f'[Profile Image Debug] UserMetaSerializer - User {user.id} avatar_url after get_image_url: {avatar_url}')
            
            # サムネイルURLを取得
            if avatar_url:
                avatar_thumbnail_url = get_thumbnail_url(avatar_url, max_size=300, quality=80)
                if avatar_thumbnail_url == avatar_url:
                    avatar_thumbnail_url = None
        
        data['avatar_url'] = avatar_url
        data['avatar_thumbnail_url'] = avatar_thumbnail_url
        
        # ヘッダーURLの取得（サムネイルは生成しない）
        header_url_raw = data.get('header_url')
        logger.info(f'[Profile Image Debug] UserMetaSerializer - User {user.id} header_url from DB: {header_url_raw}')
        
        header_url = None
        if header_url_raw:
            header_url = get_image_url(
                image_url_field=header_url_raw,
                request=request,
                verify_exists=False  # 存在確認を行わない
            )
            logger.info(f'[Profile Image Debug] UserMetaSerializer - User {user.id} header_url after get_image_url: {header_url}')
        
        data['header_url'] = header_url
        
        # Check if title is expired
        if instance.active_title and instance.expires_at:
            from django.utils import timezone
            if instance.expires_at <= timezone.now():
                # Title expired, clear it
                data['active_title'] = None
                data['expires_at'] = None
        
        # 称号のバナー画像URLを取得
        active_title = data.get('active_title')
        user = instance.user
        is_studysphere_user = bool(user.studysphere_user_id or user.studysphere_login_code)
        logger.info(f'[UserMetaSerializer] User {user.id} (StudySphere: {is_studysphere_user}) - active_title: {active_title}')
        
        if active_title:
            try:
                from gamification.models import Title
                from toybox.image_utils import get_image_url
                title_obj = Title.objects.filter(name=active_title).first()
                if title_obj:
                    data['active_title_image_url'] = get_image_url(
                        image_field=title_obj.image,
                        image_url_field=title_obj.image_url,
                        request=request,
                        verify_exists=False  # ファイルが存在しなくてもURLを返す
                    )
                    logger.info(f'[UserMetaSerializer] User {user.id} - Found title object for "{active_title}", image_url: {data["active_title_image_url"]}')
                else:
                    data['active_title_image_url'] = None
                    logger.warning(f'[UserMetaSerializer] User {user.id} - Title object not found for "{active_title}"')
            except Exception as e:
                logger.warning(f'[UserMetaSerializer] User {user.id} - Failed to get title image for {active_title}: {e}', exc_info=True)
                data['active_title_image_url'] = None
        else:
            data['active_title_image_url'] = None
            logger.info(f'[UserMetaSerializer] User {user.id} - No active_title')
        
        return data
    
    class Meta:
        model = UserMeta
        fields = ['display_id', 'url_id', 'display_name', 'avatar_url', 'active_title', 'title_color', 'expires_at', 'bio', 'header_url', 'lottery_bonus_count', 'onboarding_completed']
        read_only_fields = ['display_id', 'url_id', 'avatar_url', 'lottery_bonus_count']


class UserCardSerializer(serializers.ModelSerializer):
    """UserCard serializer."""
    card_code = serializers.CharField(source='card.code', read_only=True)
    card_name = serializers.CharField(source='card.name', read_only=True)
    card_rarity = serializers.CharField(source='card.rarity', read_only=True)
    
    class Meta:
        model = UserCard
        fields = ['id', 'card', 'card_code', 'card_name', 'card_rarity', 'obtained_at']
        read_only_fields = ['id', 'obtained_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """UserRegistration serializer."""
    
    class Meta:
        model = UserRegistration
        fields = ['address', 'age_group', 'phone']
        read_only_fields = []


class RegisterSerializer(serializers.Serializer):
    """Registration serializer."""
    username = serializers.CharField(min_length=3, max_length=30, help_text="User ID (alphanumeric and underscore)")
    display_name = serializers.CharField(min_length=1, max_length=50, required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    # StudySphere SSO fields (optional)
    studysphere_user_id = serializers.IntegerField(required=False, allow_null=True)
    studysphere_login_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_username(self, value):
        """Validate username format."""
        import re
        if not re.match(r'^[a-z0-9_]+$', value.lower()):
            raise serializers.ValidationError("Username must contain only lowercase letters, numbers, and underscores.")
        return value.lower()
    
    def validate(self, attrs):
        """Validate registration data."""
        username = attrs.get('username')
        display_name = attrs.get('display_name', '').strip()
        studysphere_user_id = attrs.get('studysphere_user_id')
        password = attrs.get('password', '').strip()
        
        # SSO経由の場合はパスワードがなくてもOK、通常の場合はパスワード必須
        if not studysphere_user_id and not password:
            raise serializers.ValidationError({'password': 'パスワードは必須です。'})
        
        # Check if username already exists
        if User.objects.filter(display_id=username).exists():
            raise serializers.ValidationError({'username': 'This username is already taken.'})
        
        # Check if StudySphere user_id already exists
        if studysphere_user_id:
            if User.objects.filter(studysphere_user_id=studysphere_user_id).exists():
                raise serializers.ValidationError({
                    'studysphere_user_id': 'このStudySphereアカウントは既に登録されています。'
                })
        
        # Use username as display_name if not provided
        if not display_name:
            attrs['display_name'] = username
        
        return attrs
    
    def create(self, validated_data):
        """Create user and UserMeta."""
        username = validated_data['username']
        password = validated_data.get('password', '').strip()
        display_name = validated_data.get('display_name', username)
        email = validated_data.get('email', '').strip() or None
        studysphere_user_id = validated_data.get('studysphere_user_id')
        studysphere_login_code = validated_data.get('studysphere_login_code', '').strip() or None
        
        # SSO経由の場合はパスワードなしでユーザーを作成
        # パスワードがない場合は、ランダムなパスワードを設定（SSO認証のみでログインするため）
        if not password and studysphere_user_id:
            import secrets
            password = secrets.token_urlsafe(32)  # ランダムなパスワードを生成（使用されない）
        
        # Create user
        role = User.Role.PAID_USER if studysphere_user_id else User.Role.FREE_USER
        user = User.objects.create_user(
            email=email,
            display_id=username,
            password=password if password else None,
            role=role,
        )
        
        # Set StudySphere fields if provided
        if studysphere_user_id:
            user.studysphere_user_id = studysphere_user_id
        if studysphere_login_code:
            user.studysphere_login_code = studysphere_login_code
        user.save()
        
        # Create UserMeta with display_name in bio field (for now, until we add a proper display_name field)
        # Note: bio field is used to store display_name temporarily
        UserMeta.objects.get_or_create(
            user=user,
            defaults={'bio': display_name}
        )
        
        return user
