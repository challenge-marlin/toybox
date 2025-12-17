"""
Custom Django Admin Site with navigation links.
"""
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import reverse


class CustomAdminSite(admin.AdminSite):
    """カスタムDjango管理サイト - カスタム管理画面へのリンクを追加"""
    
    site_header = 'ToyBox 管理サイト'
    site_title = 'ToyBox 管理'
    index_title = 'サイト管理'
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page.
        Add custom admin console link to context.
        """
        from django.conf import settings
        admin_url = getattr(settings, 'ADMIN_URL', 'admin')
        extra_context = extra_context or {}
        extra_context['custom_admin_console_url'] = f'/{admin_url}/console/'
        extra_context['discord_bot_post_url'] = f'/{admin_url}/console/discord-bot-post/'
        extra_context['toybox_home_url'] = '/'
        return super().index(request, extra_context)
    
    def each_context(self, request):
        """
        Add custom links to every admin page context.
        """
        from django.conf import settings
        admin_url = getattr(settings, 'ADMIN_URL', 'admin')
        context = super().each_context(request)
        context['custom_admin_console_url'] = f'/{admin_url}/console/'
        context['discord_bot_post_url'] = f'/{admin_url}/console/discord-bot-post/'
        context['toybox_home_url'] = '/'
        return context

