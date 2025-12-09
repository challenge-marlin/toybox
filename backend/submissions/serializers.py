"""
Submissions app serializers for DRF.
"""
import os
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
    thumbnail = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Submission
        fields = [
            'id', 'author', 'author_display_id', 'author_avatar_url',
            'image', 'display_image_url', 'thumbnail', 'thumbnail_url',
            'image_url', 'video_url', 'game_url',
            'title', 'caption', 'hashtags', 'comment_enabled', 'status',
            'active_title', 'title_color',
            'reactions_count', 'user_reacted',
            'created_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'deleted_at', 'status']
    
    def get_image(self, obj):
        """Get absolute URL for image field."""
        if obj.image:
            try:
                # ファイルの存在確認
                from django.conf import settings
                if hasattr(obj.image, 'path'):
                    if not os.path.exists(obj.image.path):
                        # ファイルが存在しない場合はNoneを返し、データベースをクリア
                        obj.image = None
                        obj.save(update_fields=['image'])
                        return None
                
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
            except (ValueError, AttributeError, OSError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to get image URL for submission {obj.id}: {str(e)}')
                return None
        
        # Fallback to image_url if image field is empty
        if obj.image_url:
            # image_urlの存在確認
            try:
                from django.conf import settings
                from urllib.parse import urlparse
                # URLからファイルパスを抽出
                if obj.image_url.startswith('http'):
                    parsed = urlparse(obj.image_url)
                    file_path = parsed.path
                else:
                    file_path = obj.image_url
                
                # /uploads/submissions/ から始まる場合、ファイルの存在確認
                if file_path.startswith('/uploads/submissions/'):
                    filename = file_path.replace('/uploads/submissions/', '')
                    full_path = settings.MEDIA_ROOT / 'submissions' / filename
                    if not full_path.exists():
                        # ファイルが存在しない場合はNoneを返し、データベースをクリア
                        obj.image_url = None
                        obj.save(update_fields=['image_url'])
                        return None
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to verify image_url for submission {obj.id}: {str(e)}')
        
        return obj.image_url or None
    
    def get_display_image_url(self, obj):
        """Get display image URL (prefer thumbnail for games, then image_url, then image field)."""
        import os
        from django.conf import settings
        from urllib.parse import urlparse
        request = self.context.get('request')
        
        # ゲームの場合はサムネイルを優先
        if obj.game_url and obj.thumbnail:
            try:
                # サムネイルファイルの存在確認
                if hasattr(obj.thumbnail, 'path'):
                    if not os.path.exists(obj.thumbnail.path):
                        # ファイルが存在しない場合はNoneを返し、データベースをクリア
                        obj.thumbnail = None
                        obj.save(update_fields=['thumbnail'])
                    else:
                        if request:
                            return request.build_absolute_uri(obj.thumbnail.url)
                        return obj.thumbnail.url
            except (ValueError, AttributeError, OSError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to get thumbnail URL for submission {obj.id}: {str(e)}')
                # フォールバック: image_urlを使用
                if obj.image_url:
                    # image_urlの存在確認
                    try:
                        if obj.image_url.startswith('http'):
                            parsed = urlparse(obj.image_url)
                            file_path = parsed.path
                        else:
                            file_path = obj.image_url
                        
                        if file_path.startswith('/uploads/submissions/'):
                            filename = file_path.replace('/uploads/submissions/', '')
                            full_path = settings.MEDIA_ROOT / 'submissions' / filename
                            if full_path.exists():
                                return obj.image_url
                            else:
                                obj.image_url = None
                                obj.save(update_fields=['image_url'])
                    except Exception:
                        pass
        
        # image_urlを優先（レガシーまたは外部URL）
        if obj.image_url:
            try:
                # image_urlの存在確認
                if obj.image_url.startswith('http'):
                    parsed = urlparse(obj.image_url)
                    file_path = parsed.path
                else:
                    file_path = obj.image_url
                
                # /uploads/submissions/ から始まる場合、ファイルの存在確認
                if file_path.startswith('/uploads/submissions/'):
                    filename = file_path.replace('/uploads/submissions/', '')
                    full_path = settings.MEDIA_ROOT / 'submissions' / filename
                    if not full_path.exists():
                        # ファイルが存在しない場合はNoneを返し、データベースをクリア
                        obj.image_url = None
                        obj.save(update_fields=['image_url'])
                        return None
                # 外部URLの場合はそのまま返す
                return obj.image_url
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to verify image_url for submission {obj.id}: {str(e)}')
        
        # imageフィールドを使用
        if obj.image:
            try:
                # ファイルの存在確認
                if hasattr(obj.image, 'path'):
                    if not os.path.exists(obj.image.path):
                        # ファイルが存在しない場合はNoneを返し、データベースをクリア
                        obj.image = None
                        obj.save(update_fields=['image'])
                        return None
                
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
            except (ValueError, AttributeError, OSError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Failed to get image URL for submission {obj.id}: {str(e)}')
        
        return None
    
    def get_thumbnail(self, obj):
        """Get absolute URL for thumbnail field."""
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Get thumbnail URL (alias for thumbnail)."""
        return self.get_thumbnail(obj)
    
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
        # annotateで追加されたreactions_countを優先的に使用
        if hasattr(obj, 'reactions_count'):
            return obj.reactions_count
        # フォールバック: 直接カウント
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
        fields = ['image', 'thumbnail', 'title', 'caption', 'hashtags', 'comment_enabled']
    
    def validate_title(self, value):
        """Validate title length."""
        if value and len(value) > 20:
            raise serializers.ValidationError('題名は20文字までです。')
        return value
    
    def validate_caption(self, value):
        """Validate caption length."""
        if value and len(value) > 140:
            raise serializers.ValidationError('キャプションは140文字までです。')
        return value
    
    def validate_hashtags(self, value):
        """Validate hashtags count."""
        if not isinstance(value, list):
            raise serializers.ValidationError('ハッシュタグは配列形式で指定してください。')
        if len(value) > 3:
            raise serializers.ValidationError('ハッシュタグは3つまでです。')
        # 各ハッシュタグが文字列であることを確認
        for tag in value:
            if not isinstance(tag, str):
                raise serializers.ValidationError('ハッシュタグは文字列で指定してください。')
        return value
    
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
