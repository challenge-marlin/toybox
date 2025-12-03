"""
Adminpanel app views for admin UI (Django templates).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime
from toybox.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated
from .models import AdminAuditLog
from users.models import User, UserMeta, UserCard, UserRegistration
from submissions.models import Submission
from sharing.models import DiscordShare


def admin_required(view_func):
    """Decorator to require admin role."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/admin/login/?next=' + request.path)
        if request.user.role != User.Role.ADMIN:
            return render(request, 'adminpanel/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
@require_http_methods(["GET"])
def dashboard(request):
    """Admin dashboard."""
    today = timezone.now().date()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    stats = {
        'today_submissions': Submission.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            deleted_at__isnull=True
        ).count(),
        'warnings_today': AdminAuditLog.objects.filter(
            created_at__gte=start,
            created_at__lte=end,
            action=AdminAuditLog.Action.WARN
        ).count(),
        'suspended_users': User.objects.filter(is_suspended=True).count(),
        'banned_users': User.objects.filter(banned_at__isnull=False).count(),
        'total_users': User.objects.count(),
        'total_submissions': Submission.objects.filter(deleted_at__isnull=True).count(),
    }
    
    return render(request, 'adminpanel/dashboard.html', {'stats': stats})


@admin_required
@require_http_methods(["GET"])
def user_list(request):
    """User list page."""
    search_query = request.GET.get('q', '')
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(display_id__icontains=search_query)
        )
    
    users = users.order_by('-created_at')[:100]
    
    return render(request, 'adminpanel/users/list.html', {
        'users': users,
        'search_query': search_query
    })


@admin_required
@require_http_methods(["GET"])
def user_detail(request, user_id):
    """User detail page."""
    user = get_object_or_404(User, id=user_id)
    
    try:
        meta = UserMeta.objects.get(user=user)
    except UserMeta.DoesNotExist:
        meta = None
    
    try:
        registration = UserRegistration.objects.get(user=user)
    except UserRegistration.DoesNotExist:
        registration = None
    
    cards = UserCard.objects.filter(user=user).select_related('card')
    submissions = Submission.objects.filter(author=user).order_by('-created_at')
    discord_shares = DiscordShare.objects.filter(user=user).order_by('-shared_at')
    audit_logs = AdminAuditLog.objects.filter(
        Q(target_user=user) | Q(actor=user)
    ).order_by('-created_at')[:50]
    
    warnings = AdminAuditLog.objects.filter(
        target_user=user,
        action=AdminAuditLog.Action.WARN
    ).order_by('-created_at')
    
    return render(request, 'adminpanel/users/detail.html', {
        'user': user,
        'meta': meta,
        'registration': registration,
        'cards': cards,
        'submissions': submissions,
        'discord_shares': discord_shares,
        'audit_logs': audit_logs,
        'warnings': warnings,
    })


@admin_required
@require_http_methods(["GET"])
def submission_list(request):
    """Submission list page."""
    include_deleted = request.GET.get('include_deleted', 'false').lower() == 'true'
    submissions = Submission.objects.all()
    
    if not include_deleted:
        submissions = submissions.filter(deleted_at__isnull=True)
    
    submissions = submissions.select_related('author').order_by('-created_at')[:100]
    
    return render(request, 'adminpanel/submissions/list.html', {
        'submissions': submissions,
        'include_deleted': include_deleted
    })


@admin_required
@require_http_methods(["GET"])
def discord_share_list(request):
    """Discord share list page."""
    user_id = request.GET.get('user')
    shares = DiscordShare.objects.all()
    
    if user_id:
        shares = shares.filter(user_id=user_id)
    
    shares = shares.select_related('user', 'submission').order_by('-shared_at')[:100]
    
    return render(request, 'adminpanel/discord_shares/list.html', {
        'shares': shares,
        'user_id': user_id
    })


@admin_required
@require_http_methods(["GET"])
def audit_log_list(request):
    """Audit log list page."""
    user_id = request.GET.get('user')
    logs = AdminAuditLog.objects.all()
    
    if user_id:
        logs = logs.filter(
            Q(target_user_id=user_id) | Q(actor_id=user_id)
        )
    
    logs = logs.select_related('actor', 'target_user', 'target_submission').order_by('-created_at')[:100]
    
    return render(request, 'adminpanel/audit_logs/list.html', {
        'logs': logs,
        'user_id': user_id
    })


@admin_required
@require_http_methods(["GET"])
def discord_bot_post(request):
    """Discord bot post page."""
    return render(request, 'adminpanel/discord_bot_post.html')

