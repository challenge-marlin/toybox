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
    list_display = ['name', 'banner_preview', 'color', 'duration_days']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'banner_preview_detail']
    fieldsets = (
        ('称号情報', {
            'fields': ('name', 'color', 'duration_days'),
            'description': '称号の名前、表示色、有効期間（日数）を設定します。'
        }),
        ('バナー画像設定', {
            'fields': ('image', 'banner_preview_detail', 'image_url'),
            'description': '称号のバナー画像（321×115px推奨）を設定します。画像ファイルをアップロードするか、外部URLを指定できます。画像ファイルが優先されます。'
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': '称号の作成日時と最終更新日時です。'
        }),
    )
    
    def banner_preview(self, obj):
        """一覧画面でバナー画像を表示します。"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 120px; max-height: 24px; object-fit: contain; border-radius: 4px;" />',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 120px; max-height: 24px; object-fit: contain; border-radius: 4px;" />',
                obj.image_url
            )
        return '-'
    banner_preview.short_description = 'バナー'
    
    def banner_preview_detail(self, obj):
        """詳細画面でバナー画像を表示します。"""
        if obj.image:
            return format_html(
                '<div style="margin-bottom: 1rem;"><img src="{}" style="max-width: 321px; max-height: 115px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" /></div>',
                obj.image.url
            )
        elif obj.image_url:
            return format_html(
                '<div style="margin-bottom: 1rem;"><img src="{}" style="max-width: 321px; max-height: 115px; object-fit: contain; border-radius: 8px; border: 1px solid #ddd;" /></div>',
                obj.image_url
            )
        return format_html('<p style="color: #999;">バナー画像が設定されていません。</p>')
    banner_preview_detail.short_description = 'バナー画像プレビュー'


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """カード管理 - ユーザーが獲得できるカードのマスタデータを管理します。"""
    list_display = ['code', 'image_preview', 'name', 'rarity', 'card_type', 'attribute_colored', 'atk_points', 'def_points', 'created_at']
    list_filter = ['rarity', 'card_type', 'created_at']
    search_fields = ['code', 'name', 'old_id', 'attribute', 'buff_effect']
    readonly_fields = ['created_at', 'updated_at', 'image_preview_detail']
    fieldsets = (
        ('カード情報', {
            'fields': ('code', 'name', 'rarity', 'card_type', 'attribute', 'atk_points', 'def_points', 'description', 'buff_effect'),
            'description': 'カードのコード、名前、レアリティ、種別（キャラ/エフェクト）、属性、ATK/DEF、カード説明、バフ効果を設定します。'
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
    
    ATTRIBUTE_COLORS = {
        '火': '#e53e3e',
        '水': '#63b3ed',
        '木': '#48bb78',
        '金': '#d69e2e',
        '土': '#a0522d',
        '光': '#ecc94b',
        '闇': '#805ad5',
    }

    def attribute_colored(self, obj):
        """一覧画面で属性を色付き表示します。"""
        a = (obj.attribute or '').strip()
        if not a:
            return '-'
        color = self.ATTRIBUTE_COLORS.get(a)
        if color:
            return format_html(
                '<span style="color: {}; font-weight: 600;">{}</span>',
                color,
                a,
            )
        return a
    attribute_colored.short_description = '属性'

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

