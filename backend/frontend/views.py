"""
Frontend app views for general UI.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime
import json


@require_http_methods(["GET"])
def index(request):
    """Home page - hero page with splash screen."""
    # 常にキービジュアルを表示（JavaScriptでJWTトークンを確認してリダイレクト）
    # Djangoセッション認証はチェックしない（JWT認証のみ）
    return render(request, 'frontend/index.html')


@require_http_methods(["GET"])
def feed(request):
    """Feed page - all submissions grid."""
    return render(request, 'frontend/feed.html')


@require_http_methods(["GET"])
def login_page(request):
    """Login page."""
    # Djangoセッション認証はチェックしない（JWT認証のみ）
    # JavaScriptでトークンをチェックしてリダイレクト
    return render(request, 'frontend/login.html')


@require_http_methods(["GET"])
def signup_page(request):
    """Signup page."""
    # Djangoセッション認証はチェックしない（JWT認証のみ）
    # JavaScriptでトークンをチェックしてリダイレクト
    return render(request, 'frontend/signup.html')


@login_required
@require_http_methods(["GET"])
def me(request):
    """My profile page - metadata display."""
    return render(request, 'frontend/me.html')


@login_required
@require_http_methods(["GET", "POST"])
def lottery(request):
    """Lottery page - draw button with result modal."""
    if request.method == 'POST':
        # Handle lottery draw
        return render(request, 'frontend/lottery.html', {'drawn': True})
    return render(request, 'frontend/lottery.html')


@login_required
@require_http_methods(["GET"])
def collection(request):
    """Collection page - user's card collection."""
    return render(request, 'frontend/collection.html')


@login_required
@require_http_methods(["GET"])
def profile(request):
    """Profile settings page."""
    return render(request, 'frontend/profile.html')


@login_required
@require_http_methods(["GET"])
def profile_view(request):
    """Profile view page - display user's profile with submissions."""
    return render(request, 'frontend/profile_view.html')

