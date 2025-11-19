"""
Lottery app models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class LotteryRule(models.Model):
    """Lottery rule configuration."""
    base_rate = models.DecimalField('基本確率', max_digits=5, decimal_places=4, default=Decimal('0.008'))
    per_submit_increment = models.DecimalField('投稿ごとの増加率', max_digits=5, decimal_places=4, default=Decimal('0.002'))
    max_rate = models.DecimalField('最大確率', max_digits=5, decimal_places=4, default=Decimal('0.05'))
    daily_cap = models.IntegerField('1日の投稿上限', default=1)
    
    is_active = models.BooleanField('有効', default=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'lottery_rules'
        verbose_name = '抽選ルール'
        verbose_name_plural = '抽選ルール'
    
    def __str__(self):
        return f'抽選ルール (基本: {self.base_rate}, 最大: {self.max_rate})'


class JackpotWin(models.Model):
    """Jackpot win record."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jackpot_wins', verbose_name='ユーザー')
    submission = models.ForeignKey('submissions.Submission', on_delete=models.SET_NULL, null=True, blank=True, related_name='jackpot_wins', verbose_name='投稿')
    won_at = models.DateTimeField('当選日時', auto_now_add=True, db_index=True)
    pinned_until = models.DateTimeField('ピン留め期限', null=True, blank=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        db_table = 'jackpot_wins'
        verbose_name = 'ジャックポット当選'
        verbose_name_plural = 'ジャックポット当選'
        indexes = [
            models.Index(fields=['won_at']),
            models.Index(fields=['user', 'won_at']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.user.display_id}のジャックポット当選 ({self.won_at})'

