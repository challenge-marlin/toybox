"""
Sharing app admin.
"""
from django.contrib import admin
from .models import DiscordShare


@admin.register(DiscordShare)
class DiscordShareAdmin(admin.ModelAdmin):
    """DiscordShare admin."""
    list_display = ['user', 'submission', 'share_channel', 'shared_at', 'message_id']
    list_filter = ['share_channel', 'shared_at']
    search_fields = ['user__email', 'user__display_id', 'share_channel', 'message_id', 'old_id']
    readonly_fields = ['shared_at']
    date_hierarchy = 'shared_at'

