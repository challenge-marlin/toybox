"""
Sharing app admin.
"""
from django.contrib import admin
from .models import DiscordShare


@admin.register(DiscordShare)
class DiscordShareAdmin(admin.ModelAdmin):
    """Discordシェア管理 - ユーザーがDiscordにシェアした投稿の記録を管理します。"""
    list_display = ['user', 'submission', 'share_channel', 'shared_at', 'message_id']
    list_filter = ['share_channel', 'shared_at']
    search_fields = ['user__email', 'user__display_id', 'share_channel', 'message_id', 'old_id']
    readonly_fields = ['shared_at']
    date_hierarchy = 'shared_at'
    fieldsets = (
        ('シェア情報', {
            'fields': ('user', 'submission', 'share_channel', 'message_id'),
            'description': 'シェアしたユーザー、対象の投稿、Discordチャンネル、メッセージIDを表示します。'
        }),
        ('日時情報', {
            'fields': ('shared_at',),
            'description': 'Discordにシェアした日時です。'
        }),
    )

