"""
Gamification app admin.
"""
from django.contrib import admin
from .models import Title, Card


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    """Title admin."""
    list_display = ['name', 'color', 'duration_days']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """Card admin."""
    list_display = ['code', 'name', 'rarity', 'created_at']
    list_filter = ['rarity', 'created_at']
    search_fields = ['code', 'name', 'old_id']
    readonly_fields = ['created_at', 'updated_at']

