"""
Adminpanel app admin.
"""
from django.contrib import admin
from .models import AdminAuditLog


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """AdminAuditLog admin."""
    list_display = ['action', 'actor', 'target_user', 'target_submission', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['actor__email', 'actor__display_id', 'target_user__email', 'target_user__display_id']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Action', {'fields': ('actor', 'action', 'target_user', 'target_submission')}),
        ('Details', {'fields': ('payload', 'created_at')}),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of audit logs."""
        return False

