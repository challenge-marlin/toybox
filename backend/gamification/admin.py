"""
Gamification app admin.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings
from .models import Title, Card


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    """称号管理 - ユーザーに付与できる称号のマスタデータを管理します。"""
    list_display = ['name', 'color', 'duration_days']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('称号情報', {
            'fields': ('name', 'color', 'duration_days'),
            'description': '称号の名前、表示色、有効期間（日数）を設定します。'
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': '称号の作成日時と最終更新日時です。'
        }),
    )


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """カード管理 - ユーザーが獲得できるカードのマスタデータを管理します。"""
    list_display = ['code', 'image_preview', 'name', 'rarity', 'created_at']
    list_filter = ['rarity', 'created_at']
    search_fields = ['code', 'name', 'old_id']
    readonly_fields = ['created_at', 'updated_at', 'image_preview_detail']
    fieldsets = (
        ('カード情報', {
            'fields': ('code', 'name', 'rarity', 'description'),
            'description': 'カードのコード、名前、レアリティ、説明を設定します。'
        }),
        ('画像設定', {
            'fields': ('image', 'image_preview_detail', 'image_url'),
            'description': 'カードの画像を設定します。画像ファイルをアップロードするか、外部URLを指定できます。画像ファイルが優先されます。'
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': 'カードの作成日時と最終更新日時です。'
        }),
        ('ETL追跡', {
            'fields': ('old_id',),
            'description': 'データ移行時の旧IDを記録します。',
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """一覧画面で画像を表示します。"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 60px; max-height: 60px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return '-'
    image_preview.short_description = '画像'
    
    def image_preview_detail(self, obj):
        """詳細画面で画像を表示します。"""
        if obj.image:
            return format_html(
                '<div style="margin-bottom: 1rem;"><img src="{}" style="max-width: 300px; max-height: 300px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" /></div>',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<div style="margin-bottom: 1rem;"><img src="{}" style="max-width: 300px; max-height: 300px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" /></div>',
                obj.image_url
            )
        return format_html('<p style="color: #999;">画像が設定されていません。</p>')
    image_preview_detail.short_description = '画像プレビュー'

