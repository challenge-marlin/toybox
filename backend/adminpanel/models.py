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
        WARN = 'WARN', 'Warn'
        SUSPEND = 'SUSPEND', 'Suspend'
        UNSUSPEND = 'UNSUSPEND', 'Unsuspend'
        BAN = 'BAN', 'Ban'
        UNBAN = 'UNBAN', 'Unban'
        DELETE = 'DELETE', 'Delete'
        RESTORE = 'RESTORE', 'Restore'
        RESET_PASSWORD = 'RESET_PASSWORD', 'Reset Password'
        EDIT_PROFILE = 'EDIT_PROFILE', 'Edit Profile'
        IMPORT = 'IMPORT', 'Import'
    
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs_acted')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs_targeted')
    target_submission = models.ForeignKey('submissions.Submission', on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=Action.choices)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'admin_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['actor', '-created_at']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.action} by {self.actor} at {self.created_at}'

