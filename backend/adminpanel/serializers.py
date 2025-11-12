"""
Adminpanel app serializers for DRF.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import AdminAuditLog
from users.models import UserMeta, UserCard, UserRegistration
from submissions.models import Submission
from sharing.models import DiscordShare

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    """Admin user list serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'display_id', 'role', 'avatar_url', 'is_suspended', 'banned_at', 'warning_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class AdminUserDetailSerializer(serializers.ModelSerializer):
    """Admin user detail serializer."""
    meta = serializers.SerializerMethodField()
    registration = serializers.SerializerMethodField()
    cards_count = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'display_id', 'role', 'avatar_url',
            'is_suspended', 'banned_at', 'warning_count', 'warning_notes',
            'meta', 'registration', 'cards_count', 'submissions_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_meta(self, obj):
        """Get user meta."""
        try:
            meta = UserMeta.objects.get(user=obj)
            return {
                'active_title': meta.active_title,
                'title_color': meta.title_color,
                'expires_at': meta.expires_at.isoformat() if meta.expires_at else None,
                'lottery_bonus_count': meta.lottery_bonus_count
            }
        except UserMeta.DoesNotExist:
            return None
    
    def get_registration(self, obj):
        """Get user registration."""
        try:
            reg = UserRegistration.objects.get(user=obj)
            return {
                'address': reg.address,
                'age_group': reg.age_group,
                'phone': reg.phone
            }
        except UserRegistration.DoesNotExist:
            return None
    
    def get_cards_count(self, obj):
        """Get user cards count."""
        return UserCard.objects.filter(user=obj).count()
    
    def get_submissions_count(self, obj):
        """Get user submissions count."""
        return Submission.objects.filter(author=obj, deleted_at__isnull=True).count()


class AdminSubmissionSerializer(serializers.ModelSerializer):
    """Admin submission serializer."""
    author_email = serializers.CharField(source='author.email', read_only=True)
    author_display_id = serializers.CharField(source='author.display_id', read_only=True)
    
    class Meta:
        model = Submission
        fields = [
            'id', 'author', 'author_email', 'author_display_id',
            'image', 'caption', 'comment_enabled', 'status',
            'deleted_at', 'delete_reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AdminDiscordShareSerializer(serializers.ModelSerializer):
    """Admin Discord share serializer."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_display_id = serializers.CharField(source='user.display_id', read_only=True)
    submission_id = serializers.IntegerField(source='submission.id', read_only=True)
    
    class Meta:
        model = DiscordShare
        fields = [
            'id', 'user', 'user_email', 'user_display_id',
            'submission', 'submission_id',
            'share_channel', 'message_id', 'shared_at'
        ]
        read_only_fields = ['id', 'shared_at']


class AdminAuditLogSerializer(serializers.ModelSerializer):
    """Admin audit log serializer."""
    actor_email = serializers.CharField(source='actor.email', read_only=True)
    actor_display_id = serializers.CharField(source='actor.display_id', read_only=True)
    target_user_email = serializers.CharField(source='target_user.email', read_only=True, allow_null=True)
    target_user_display_id = serializers.CharField(source='target_user.display_id', read_only=True, allow_null=True)
    
    class Meta:
        model = AdminAuditLog
        fields = [
            'id', 'actor', 'actor_email', 'actor_display_id',
            'target_user', 'target_user_email', 'target_user_display_id',
            'target_submission', 'action', 'payload', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

