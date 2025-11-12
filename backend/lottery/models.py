"""
Lottery app models.
"""
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


class LotteryRule(models.Model):
    """Lottery rule configuration."""
    base_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.008'))
    per_submit_increment = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.002'))
    max_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.05'))
    daily_cap = models.IntegerField(default=1)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lottery_rules'
    
    def __str__(self):
        return f'Lottery Rule (base: {self.base_rate}, max: {self.max_rate})'


class JackpotWin(models.Model):
    """Jackpot win record."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jackpot_wins')
    submission = models.ForeignKey('submissions.Submission', on_delete=models.SET_NULL, null=True, blank=True, related_name='jackpot_wins')
    won_at = models.DateTimeField(auto_now_add=True, db_index=True)
    pinned_until = models.DateTimeField(null=True, blank=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    class Meta:
        db_table = 'jackpot_wins'
        indexes = [
            models.Index(fields=['won_at']),
            models.Index(fields=['user', 'won_at']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'JackpotWin for {self.user.display_id} at {self.won_at}'

