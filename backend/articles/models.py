"""
Articles app models - Ver 2.22
"""
import uuid
from django.db import models
from django.conf import settings


def article_thumbnail_upload(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f'articles/thumbnails/{uuid.uuid4().hex}.{ext}'


def article_media_upload(instance, filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return f'articles/media/{uuid.uuid4().hex}.{ext}'


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', '下書き'
        PUBLISHED = 'published', '公開'

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name='著者',
    )
    title = models.CharField('タイトル', max_length=200)
    slug = models.SlugField('スラッグ', max_length=250, unique=True, blank=True)
    thumbnail = models.ImageField(
        'サムネイル', upload_to=article_thumbnail_upload, blank=True, null=True
    )
    thumbnail_url = models.URLField('サムネイルURL', max_length=500, blank=True, null=True)
    # ブロックエディタの本文 (JSON)
    body = models.JSONField('本文ブロック', default=list, blank=True)
    # カスタムCSS（XSSはテンプレート側でスコープ隔離）
    custom_css = models.TextField('カスタムCSS', blank=True)
    status = models.CharField(
        'ステータス', max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField('公開日時', null=True, blank=True)
    # 初回公開時のPT付与済みフラグ（二重付与防止）
    pt_awarded = models.BooleanField('PT付与済み', default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'articles'
        verbose_name = '記事'
        verbose_name_plural = '記事'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def get_thumbnail_url(self):
        if self.thumbnail and self.thumbnail.name:
            try:
                return self.thumbnail.url
            except Exception:
                pass
        return self.thumbnail_url or None


class ArticleReaction(models.Model):
    """記事へのリアクション（submissions.Reaction と同型）。"""

    class Type(models.TextChoices):
        SUBMIT_MEDAL = 'submit_medal', 'いいね！'
        AWESOME = 'awesome', 'すごい！'
        CUTE = 'cute', 'かわいい！'
        FUNNY = 'funny', '笑える！'
        MOVED = 'moved', '感動した'
        COOL = 'cool', 'かっこいい！'
        BEAUTIFUL = 'beautiful', 'きれい'
        EMOTIONAL = 'emotional', 'エモい！'
        GOD_GAME = 'god_game', '神ゲー！'

    EMOJI_MAP = {
        'submit_medal': '👍',
        'awesome': '🤩',
        'cute': '🥰',
        'funny': '😂',
        'moved': '😭',
        'cool': '😎',
        'beautiful': '✨',
        'emotional': '🥹',
        'god_game': '🎮',
    }

    type = models.CharField('リアクションタイプ', max_length=50, choices=Type.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_reactions',
        verbose_name='ユーザー',
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='記事',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_reactions'
        verbose_name = '記事リアクション'
        verbose_name_plural = '記事リアクション'
        unique_together = [['user', 'article', 'type']]
        indexes = [
            models.Index(fields=['article', 'type']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.type} on article {self.article_id}'


class ArticleMedia(models.Model):
    """記事内メディア（画像・動画）のアップロード管理。"""

    class MediaType(models.TextChoices):
        IMAGE = 'image', '画像'
        VIDEO = 'video', '動画'

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_media',
    )
    file = models.FileField('ファイル', upload_to=article_media_upload)
    media_type = models.CharField('種別', max_length=10, choices=MediaType.choices)
    original_name = models.CharField('元ファイル名', max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_media'
        verbose_name = '記事メディア'
        verbose_name_plural = '記事メディア'

    def __str__(self):
        return f'{self.media_type}:{self.original_name}'
