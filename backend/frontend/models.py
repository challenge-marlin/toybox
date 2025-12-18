"""
Frontend app models - Announcements.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Announcement(models.Model):
    """Announcement model for displaying notices to users."""
    
    title = models.CharField(max_length=200, verbose_name='タイトル')
    content = models.TextField(verbose_name='内容')
    is_active = models.BooleanField(default=True, verbose_name='有効')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements_created', verbose_name='作成者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'announcements'
        ordering = ['-created_at']
        verbose_name = 'お知らせ'
        verbose_name_plural = 'お知らせ'
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.title} ({self.created_at.strftime("%Y-%m-%d")})'


class SiteMaintenance(models.Model):
    """
    Site-wide maintenance flag.

    - Singleton運用（id=1 を想定）
    - Django Admin のヘッダーからワンボタンで ON/OFF できる
    """

    enabled = models.BooleanField(default=False, verbose_name='メンテナンス中')
    message = models.TextField(blank=True, default='', verbose_name='メッセージ', help_text='メンテナンス画面に表示する追加メッセージ（任意）')
    scheduled_end = models.DateTimeField(null=True, blank=True, verbose_name='終了予定', help_text='メンテナンス終了予定（任意）')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        db_table = 'site_maintenance'
        verbose_name = 'メンテナンス設定'
        verbose_name_plural = 'メンテナンス設定'

    def __str__(self):
        return 'メンテナンス: ON' if self.enabled else 'メンテナンス: OFF'

    @classmethod
    def get_solo(cls):
        """
        Singleton accessor.

        NOTE:
        以前は pk=1 を固定で作成していましたが、PostgreSQLのシーケンスが進まず
        Adminの「追加」で pk 衝突が起きるケースがあるため、pk固定はしません。
        """
        obj = cls.objects.order_by('id').first()
        if obj:
            return obj
        return cls.objects.create(enabled=False)