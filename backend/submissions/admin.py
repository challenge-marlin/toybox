"""
Submissions app admin.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from .models import Submission, Reaction


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """投稿管理 - ユーザーが投稿した画像・動画・ゲームの管理ができます。"""
    list_display = ['id', 'image_preview', 'author', 'caption', 'status', 'deleted_at', 'created_at']
    list_filter = ['status', 'deleted_at', 'created_at', 'comment_enabled']
    search_fields = ['author__email', 'author__display_id', 'caption', 'old_id']
    readonly_fields = ['created_at', 'updated_at', 'image_preview_detail', 'video_preview', 'game_link']
    date_hierarchy = 'created_at'
    
    def image_preview(self, obj):
        """一覧画面で画像を表示します。"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 80px; max-height: 80px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 80px; max-height: 80px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        elif obj.video_url:
            return format_html(
                '<div style="width: 80px; height: 80px; background: #333; display: flex; align-items: center; justify-content: center; border-radius: 4px; color: white; font-size: 12px;">動画</div>'
            )
        elif obj.game_url:
            return format_html(
                '<div style="width: 80px; height: 80px; background: #5865F2; display: flex; align-items: center; justify-content: center; border-radius: 4px; color: white; font-size: 12px;">ゲーム</div>'
            )
        return '-'
    image_preview.short_description = 'プレビュー'
    
    def image_preview_detail(self, obj):
        """詳細画面で画像を表示します。"""
        if obj.image:
            return format_html(
                '<div style="margin-bottom: 1rem;"><img src="{}" style="max-width: 500px; max-height: 500px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" /></div>',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<div style="margin-bottom: 1rem;"><img src="{}" style="max-width: 500px; max-height: 500px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" /></div>',
                obj.image_url
            )
        return '-'
    image_preview_detail.short_description = '画像プレビュー'
    
    def video_preview(self, obj):
        """詳細画面で動画を表示します。"""
        if obj.video_url:
            return format_html(
                '<div style="margin-bottom: 1rem;"><video src="{}" controls style="max-width: 500px; max-height: 500px; border-radius: 8px; border: 1px solid #ddd;"></video></div>',
                obj.video_url
            )
        return '-'
    video_preview.short_description = '動画プレビュー'
    
    def game_link(self, obj):
        """詳細画面でゲームリンクを表示します。"""
        if obj.game_url:
            return format_html(
                '<div style="margin-bottom: 1rem;"><a href="{}" target="_blank" style="display: inline-block; padding: 0.5rem 1rem; background: #5865F2; color: white; text-decoration: none; border-radius: 4px;">ゲームを開く</a></div>',
                obj.game_url
            )
        return '-'
    game_link.short_description = 'ゲームリンク'
    
    fieldsets = (
        ('投稿内容', {
            'fields': ('author', 'image', 'image_preview_detail', 'caption', 'comment_enabled'),
            'description': '投稿者、画像、キャプション、コメント機能の有効/無効を設定します。'
        }),
        ('動画・ゲーム', {
            'fields': ('video_url', 'video_preview', 'game_url', 'game_link'),
            'description': '動画URLとゲームURLを設定します。',
            'classes': ('collapse',)
        }),
        ('ステータス管理', {
            'fields': ('status', 'deleted_at', 'delete_reason'),
            'description': '投稿の公開状態、削除状態、削除理由を管理します。'
        }),
        ('レガシーフィールド', {
            'fields': ('aim', 'steps', 'frame_type', 'image_url', 'jp_result', 'likes_count'),
            'description': 'データ移行時の互換性のためのフィールドです。',
            'classes': ('collapse',)
        }),
        ('ETL追跡', {
            'fields': ('old_id',),
            'description': 'データ移行時の旧IDを記録します。',
            'classes': ('collapse',)
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': '投稿の作成日時と最終更新日時です。'
        }),
    )


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    """リアクション管理 - ユーザーが投稿に対して行ったリアクション（いいねなど）を管理します。"""
    list_display = ['user', 'submission', 'type', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['user__email', 'user__display_id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('リアクション情報', {
            'fields': ('user', 'submission', 'type'),
            'description': 'リアクションを行ったユーザー、対象の投稿、リアクションタイプを設定します。'
        }),
        ('日時情報', {
            'fields': ('created_at',),
            'description': 'リアクションの作成日時です。'
        }),
    )
