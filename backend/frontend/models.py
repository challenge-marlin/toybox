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

