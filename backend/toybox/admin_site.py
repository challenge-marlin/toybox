"""
Custom Django Admin Site with navigation links.
"""
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import reverse
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.contrib import messages
from django.shortcuts import redirect


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
        # Maintenance status (used by admin header one-button)
        try:
            from frontend.models import SiteMaintenance
            context['maintenance_enabled'] = SiteMaintenance.get_solo().enabled
        except Exception:
            context['maintenance_enabled'] = False
        context['maintenance_toggle_url'] = reverse('admin:maintenance-toggle', current_app=self.name)
        return context

    def logout(self, request, extra_context=None):
        """
        Admin logout handler.

        NOTE:
        In this project we have a separate JWT-based login for the main UI (`/login/`),
        and Django Admin uses session authentication.
        To avoid client-side scripts on the public site from interfering after admin logout,
        we always redirect to the Django Admin login screen after logout.
        """
        extra_context = extra_context or {}
        extra_context.update(self.each_context(request))

        return LogoutView.as_view(
            extra_context=extra_context,
            next_page=reverse('admin:login', current_app=self.name),
        )(request)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'maintenance/toggle/',
                self.admin_view(self.maintenance_toggle_view),
                name='maintenance-toggle',
            ),
        ]
        return custom_urls + urls

    def maintenance_toggle_view(self, request):
        # POST only (one-button)
        if request.method != 'POST':
            return redirect(reverse('admin:index', current_app=self.name))

        from frontend.models import SiteMaintenance
        s = SiteMaintenance.get_solo()
        s.enabled = not s.enabled
        s.save(update_fields=['enabled', 'updated_at'])

        if s.enabled:
            messages.warning(request, 'メンテナンスモードを ON にしました（一般ページはメンテ画面になります）')
        else:
            messages.success(request, 'メンテナンスモードを OFF にしました（通常表示に戻ります）')

        return redirect(request.META.get('HTTP_REFERER') or reverse('admin:index', current_app=self.name))

