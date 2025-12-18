"""
Frontend app admin.
"""
from django.contrib import admin
from .models import Announcement, SiteMaintenance


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """お知らせ管理 - ユーザーに表示するお知らせの作成・編集・削除ができます。"""
    list_display = ['title', 'is_active', 'created_by', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']  # 一覧画面で有効/無効を直接切り替え可能に
    
    fieldsets = (
        ('基本情報', {
            'fields': ('title', 'content', 'is_active'),
            'description': 'お知らせのタイトル、内容、表示状態を設定します。is_activeをONにすると、マイページに表示されます。'
        }),
        ('管理情報', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'description': 'お知らせの作成者、作成日時、最終更新日時です。',
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if not set."""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SiteMaintenance)
class SiteMaintenanceAdmin(admin.ModelAdmin):
    """メンテナンス設定（通常は管理画面ヘッダーのワンボタンでON/OFF）"""
    list_display = ['enabled', 'updated_at']
    readonly_fields = ['updated_at']
    fieldsets = (
        ('メンテナンス', {
            'fields': ('enabled', 'message', 'scheduled_end'),
            'description': 'サイト全体のメンテナンス切替です。enabled をONにすると一般ページはメンテナンス画面になります。',
        }),
        ('管理情報', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        # Singleton運用: 既に1件でも存在する場合は「追加」を禁止
        return not SiteMaintenance.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # 事故防止（基本削除させない）
        return False

