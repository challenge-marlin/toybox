"""
Users app admin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserRegistration, UserMeta, UserCard

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User admin."""
    list_display = ['email', 'display_id', 'role', 'is_suspended', 'warning_count', 'is_active', 'is_staff']
    list_filter = ['role', 'is_suspended', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'display_id', 'old_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['email']  # Use email instead of username
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {'fields': ('display_id', 'role', 'avatar_url')}),
        ('Moderation', {'fields': ('is_suspended', 'banned_at', 'warning_count', 'warning_notes')}),
        ('ETL Tracking', {'fields': ('old_id',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('display_id', 'role')}),
    )


@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    """UserRegistration admin."""
    list_display = ['user', 'age_group', 'created_at']
    search_fields = ['user__email', 'user__display_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserMeta)
class UserMetaAdmin(admin.ModelAdmin):
    """UserMeta admin."""
    list_display = ['user', 'active_title', 'title_color', 'expires_at', 'lottery_bonus_count']
    search_fields = ['user__email', 'user__display_id', 'old_id']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['expires_at']


@admin.register(UserCard)
class UserCardAdmin(admin.ModelAdmin):
    """UserCard admin."""
    list_display = ['user', 'card', 'obtained_at']
    search_fields = ['user__email', 'user__display_id', 'card__code']
    list_filter = ['obtained_at', 'card__rarity']
    readonly_fields = ['obtained_at']
