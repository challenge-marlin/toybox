"""
Submissions app serializers for DRF.
"""
from rest_framework import serializers
from .models import Submission, Reaction
from users.models import UserMeta


class SubmissionSerializer(serializers.ModelSerializer):
    """Submission serializer."""
    author_display_id = serializers.CharField(source='author.display_id', read_only=True)
    author_avatar_url = serializers.CharField(source='author.avatar_url', read_only=True)
    active_title = serializers.SerializerMethodField()
    title_color = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    user_reacted = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    display_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'author', 'author_display_id', 'author_avatar_url',
            'image', 'display_image_url', 'image_url', 'video_url', 'game_url',
            'caption', 'comment_enabled', 'status',
            'active_title', 'title_color',
            'reactions_count', 'user_reacted',
            'created_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'deleted_at', 'status']
    
    def get_image(self, obj):
        """Get absolute URL for image field."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        # Fallback to image_url if image field is empty
        return obj.image_url or None
    
    def get_display_image_url(self, obj):
        """Get display image URL (prefer image_url, then image field)."""
        if obj.image_url:
            return obj.image_url
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_active_title(self, obj):
        """Get author's active title."""
        from django.utils import timezone
        try:
            meta = UserMeta.objects.get(user=obj.author)
            if meta.expires_at and meta.expires_at > timezone.now():
                return meta.active_title
        except UserMeta.DoesNotExist:
            pass
        return None
    
    def get_title_color(self, obj):
        """Get author's title color."""
        from django.utils import timezone
        try:
            meta = UserMeta.objects.get(user=obj.author)
            if meta.expires_at and meta.expires_at > timezone.now():
                return meta.title_color
        except UserMeta.DoesNotExist:
            pass
        return None
    
    def get_reactions_count(self, obj):
        """Get reactions count."""
        return obj.reactions.filter(type=Reaction.Type.SUBMIT_MEDAL).count()
    
    def get_user_reacted(self, obj):
        """Check if current user has reacted."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(user=request.user, type=Reaction.Type.SUBMIT_MEDAL).exists()
        return False


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating submissions."""
    
    class Meta:
        model = Submission
        fields = ['image', 'caption', 'comment_enabled']
    
    def create(self, validated_data):
        """Create submission with current user as author."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ReactionSerializer(serializers.ModelSerializer):
    """Reaction serializer."""
    
    class Meta:
        model = Reaction
        fields = ['id', 'type', 'user', 'submission', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        """Create reaction with current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
