"""
Articles app serializers - Ver 2.20
"""
import re
import uuid
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import serializers
from .models import Article, ArticleReaction, ArticleMedia


def _make_unique_slug(title: str, exclude_pk=None) -> str:
    base = slugify(title, allow_unicode=True) or uuid.uuid4().hex[:12]
    slug = base
    n = 1
    qs = Article.objects.filter(slug=slug)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.exists():
        slug = f'{base}-{n}'
        n += 1
        qs = Article.objects.filter(slug=slug)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
    return slug


# CSSサニタイズ: script / expression / url(javascript: など危険パターンを除去
_CSS_DANGEROUS = re.compile(
    r'(expression\s*\(|javascript\s*:|@import|behavior\s*:|binding\s*:)',
    re.IGNORECASE,
)


def sanitize_css(css: str) -> str:
    """危険なCSSパターンを除去する（XSS対策）。"""
    return _CSS_DANGEROUS.sub('/* removed */', css)


class ArticleSerializer(serializers.ModelSerializer):
    author_display_id = serializers.SerializerMethodField()
    author_avatar_url = serializers.SerializerMethodField()
    thumbnail_url_resolved = serializers.SerializerMethodField()
    all_reactions = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    user_reacted = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug',
            'author', 'author_display_id', 'author_avatar_url',
            'thumbnail_url_resolved',
            'body', 'custom_css', 'status', 'published_at',
            'all_reactions', 'reactions_count', 'user_reacted',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'author', 'published_at', 'created_at', 'updated_at']

    def get_author_display_id(self, obj):
        return obj.author.display_id

    def get_author_avatar_url(self, obj):
        return obj.author.avatar_url or None

    def get_thumbnail_url_resolved(self, obj):
        request = self.context.get('request')
        url = obj.get_thumbnail_url()
        if url and request and url.startswith('/'):
            return request.build_absolute_uri(url)
        return url

    def get_reactions_count(self, obj):
        return obj.reactions.filter(type=ArticleReaction.Type.SUBMIT_MEDAL).count()

    def get_user_reacted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reactions.filter(
                user=request.user, type=ArticleReaction.Type.SUBMIT_MEDAL
            ).exists()
        return False

    def get_all_reactions(self, obj):
        request = self.context.get('request')
        current_user = request.user if request and request.user.is_authenticated else None
        result = []
        for rtype in ArticleReaction.Type:
            count = obj.reactions.filter(type=rtype).count()
            user_reacted = False
            if current_user:
                user_reacted = obj.reactions.filter(user=current_user, type=rtype).exists()
            result.append({
                'type': rtype.value,
                'label': rtype.label,
                'emoji': ArticleReaction.EMOJI_MAP.get(rtype.value, '👍'),
                'count': count,
                'user_reacted': user_reacted,
            })
        return result


class ArticleWriteSerializer(serializers.ModelSerializer):
    """記事の作成・更新用。"""

    class Meta:
        model = Article
        fields = ['title', 'body', 'custom_css', 'status', 'thumbnail', 'thumbnail_url']

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('タイトルを入力してください。')
        return value.strip()

    def validate_custom_css(self, value):
        return sanitize_css(value or '')

    def validate_status(self, value):
        allowed = [Article.Status.DRAFT, Article.Status.PUBLISHED]
        if value not in [s.value for s in allowed]:
            raise serializers.ValidationError('不正なステータスです。')
        return value

    def _award_article_pt(self, article):
        """初回公開時にPTを付与する（3.0 PT）。"""
        if article.pt_awarded:
            return
        if article.status != Article.Status.PUBLISHED:
            return
        from gamification.services import award_points
        from gamification.models import PointHistory
        try:
            award_points(
                article.author,
                'article_published',  # PointHistory.ActionType に追加するか文字列で記録
                3,
                '記事初回公開',
            )
        except Exception:
            import logging
            logging.getLogger(__name__).exception('article pt award failed')
        article.pt_awarded = True

    def create(self, validated_data):
        from django.utils import timezone as tz
        validated_data['author'] = self.context['request'].user
        status_val = validated_data.get('status', Article.Status.DRAFT)
        if status_val == Article.Status.PUBLISHED:
            validated_data['published_at'] = tz.now()
        # slug 生成
        validated_data['slug'] = _make_unique_slug(validated_data.get('title', ''))
        article = super().create(validated_data)
        self._award_article_pt(article)
        article.save(update_fields=['pt_awarded'])
        return article

    def update(self, instance, validated_data):
        from django.utils import timezone as tz
        new_status = validated_data.get('status', instance.status)
        # 初回公開
        if new_status == Article.Status.PUBLISHED and instance.status != Article.Status.PUBLISHED:
            validated_data['published_at'] = tz.now()
        # タイトルが変わったらslug再生成
        new_title = validated_data.get('title', instance.title)
        if new_title != instance.title:
            validated_data['slug'] = _make_unique_slug(new_title, exclude_pk=instance.pk)
        article = super().update(instance, validated_data)
        self._award_article_pt(article)
        article.save(update_fields=['pt_awarded', 'slug'])
        return article


class ArticleMediaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ArticleMedia
        fields = ['id', 'url', 'media_type', 'original_name', 'created_at']

    def get_url(self, obj):
        request = self.context.get('request')
        try:
            url = obj.file.url
            if request and url.startswith('/'):
                return request.build_absolute_uri(url)
            return url
        except Exception:
            return None
