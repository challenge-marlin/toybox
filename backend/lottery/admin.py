"""
Lottery app admin.
"""
from django.contrib import admin
from .models import LotteryRule, JackpotWin


@admin.register(LotteryRule)
class LotteryRuleAdmin(admin.ModelAdmin):
    """LotteryRule admin."""
    list_display = ['id', 'base_rate', 'per_submit_increment', 'max_rate', 'daily_cap', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JackpotWin)
class JackpotWinAdmin(admin.ModelAdmin):
    """JackpotWin admin."""
    list_display = ['user', 'submission', 'won_at', 'pinned_until']
    list_filter = ['won_at', 'pinned_until']
    search_fields = ['user__email', 'user__display_id', 'old_id']
    readonly_fields = ['won_at']
    date_hierarchy = 'won_at'

