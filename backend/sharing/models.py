"""
Sharing app models.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DiscordShare(models.Model):
    """Discord share record."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discord_shares', verbose_name='ユーザー')
    submission = models.ForeignKey('submissions.Submission', on_delete=models.SET_NULL, null=True, blank=True, related_name='discord_shares', verbose_name='投稿')
    shared_at = models.DateTimeField('シェア日時', auto_now_add=True, db_index=True)
    share_channel = models.CharField('チャンネル', max_length=100)
    message_id = models.CharField('メッセージID', max_length=100, blank=True, null=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        db_table = 'discord_shares'
        verbose_name = 'Discordシェア'
        verbose_name_plural = 'Discordシェア'
        indexes = [
            models.Index(fields=['shared_at']),
            models.Index(fields=['user', 'shared_at']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.user.display_id}のDiscordシェア ({self.shared_at})'

