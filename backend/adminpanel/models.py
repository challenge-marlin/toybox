"""
Adminpanel app models - Audit logging.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class AdminAuditLog(models.Model):
    """Admin audit log for tracking all administrative actions."""
    
    class Action(models.TextChoices):
        WARN = 'WARN', '警告'
        SUSPEND = 'SUSPEND', 'アカウント停止'
        UNSUSPEND = 'UNSUSPEND', 'アカウント停止解除'
        BAN = 'BAN', 'BAN'
        UNBAN = 'UNBAN', 'BAN解除'
        DELETE = 'DELETE', '削除'
        RESTORE = 'RESTORE', '復元'
        RESET_PASSWORD = 'RESET_PASSWORD', 'パスワードリセット'
        EDIT_PROFILE = 'EDIT_PROFILE', 'プロフィール編集'
        IMPORT = 'IMPORT', 'インポート'
    
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs_acted', verbose_name='実行者')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs_targeted', verbose_name='対象ユーザー')
    target_submission = models.ForeignKey('submissions.Submission', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs', verbose_name='対象投稿')
    action = models.CharField('アクション', max_length=50, choices=Action.choices)
    payload = models.JSONField('詳細情報', default=dict, blank=True)
    created_at = models.DateTimeField('実行日時', auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'admin_audit_logs'
        verbose_name = '管理操作ログ'
        verbose_name_plural = '管理操作ログ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.get_action_display()} by {self.actor} at {self.created_at}'

