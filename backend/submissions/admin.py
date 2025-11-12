"""
Submissions app admin.
"""
from django.contrib import admin
from .models import Submission, Reaction


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Submission admin."""
    list_display = ['id', 'author', 'caption', 'status', 'deleted_at', 'created_at']
    list_filter = ['status', 'deleted_at', 'created_at', 'comment_enabled']
    search_fields = ['author__email', 'author__display_id', 'caption', 'old_id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Content', {'fields': ('author', 'image', 'caption', 'comment_enabled')}),
        ('Status', {'fields': ('status', 'deleted_at', 'delete_reason')}),
        ('Legacy Fields', {'fields': ('aim', 'steps', 'frame_type', 'image_url', 'video_url', 'game_url', 'jp_result', 'likes_count'), 'classes': ('collapse',)}),
        ('ETL Tracking', {'fields': ('old_id',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    """Reaction admin."""
    list_display = ['user', 'submission', 'type', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['user__email', 'user__display_id']
    readonly_fields = ['created_at']
