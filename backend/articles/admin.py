"""
Articles app admin - Ver 2.22
"""
from django.contrib import admin
from .models import Article, ArticleReaction, ArticleMedia


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'status', 'pt_awarded', 'published_at', 'created_at']
    list_filter = ['status', 'pt_awarded']
    search_fields = ['title', 'author__display_id']
    readonly_fields = ['pt_awarded', 'published_at', 'created_at', 'updated_at']


@admin.register(ArticleReaction)
class ArticleReactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'article', 'user', 'type', 'created_at']
    list_filter = ['type']


@admin.register(ArticleMedia)
class ArticleMediaAdmin(admin.ModelAdmin):
    list_display = ['id', 'uploader', 'media_type', 'original_name', 'created_at']
