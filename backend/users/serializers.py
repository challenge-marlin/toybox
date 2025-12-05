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
    
    class Meta:
        model = User
        fields = ['id', 'email', 'display_id', 'role', 'avatar_url', 'is_suspended', 'banned_at', 'warning_count']
        read_only_fields = ['id', 'role', 'is_suspended', 'banned_at', 'warning_count']


class UserMetaSerializer(serializers.ModelSerializer):
    """UserMeta serializer."""
    display_id = serializers.CharField(source='user.display_id', read_only=True)
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.URLField(source='user.avatar_url', read_only=True)
    
    def get_display_name(self, obj):
        """Get display name from display_name field, fallback to bio, then display_id."""
        return obj.display_name or obj.bio or obj.user.display_id
    
    def to_representation(self, instance):
        """Override to check title expiry."""
        data = super().to_representation(instance)
        
        # Check if title is expired
        if instance.active_title and instance.expires_at:
            from django.utils import timezone
            if instance.expires_at <= timezone.now():
                # Title expired, clear it
                data['active_title'] = None
                data['expires_at'] = None
        
        return data
    
    class Meta:
        model = UserMeta
        fields = ['display_id', 'display_name', 'avatar_url', 'active_title', 'title_color', 'expires_at', 'bio', 'header_url', 'lottery_bonus_count', 'onboarding_completed']
        read_only_fields = ['display_id', 'avatar_url', 'lottery_bonus_count']


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
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    
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
        
        # Check if username already exists
        if User.objects.filter(display_id=username).exists():
            raise serializers.ValidationError({'username': 'This username is already taken.'})
        
        # Use username as display_name if not provided
        if not display_name:
            attrs['display_name'] = username
        
        return attrs
    
    def create(self, validated_data):
        """Create user and UserMeta."""
        username = validated_data['username']
        password = validated_data['password']
        display_name = validated_data.get('display_name', username)
        email = validated_data.get('email', '').strip() or None
        
        # Create user
        user = User.objects.create_user(
            email=email,
            display_id=username,
            password=password
        )
        
        # Create UserMeta with display_name in bio field (for now, until we add a proper display_name field)
        # Note: bio field is used to store display_name temporarily
        UserMeta.objects.get_or_create(
            user=user,
            defaults={'bio': display_name}
        )
        
        return user
