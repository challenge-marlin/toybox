"""
Adminpanel app admin.
"""
from django.contrib import admin
from .models import AdminAuditLog


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """管理操作ログ - 管理者が行ったすべての操作（ユーザー停止、BAN、削除など）の記録を閲覧できます。"""
    list_display = ['action', 'actor', 'target_user', 'target_submission', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['actor__email', 'actor__display_id', 'target_user__email', 'target_user__display_id']
    readonly_fields = ['created_at', 'actor', 'action', 'target_user', 'target_submission', 'payload']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('操作情報', {
            'fields': ('actor', 'action', 'target_user', 'target_submission'),
            'description': '操作を実行した管理者、実行したアクション、対象のユーザー・投稿を表示します。'
        }),
        ('詳細情報', {
            'fields': ('payload', 'created_at'),
            'description': '操作の詳細情報（JSON形式）と実行日時を表示します。'
        }),
    )
    
    def has_add_permission(self, request):
        """ログの手動作成を無効化（システムが自動的に作成します）。"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """ログの編集を無効化（変更不可です）。"""
        return False

