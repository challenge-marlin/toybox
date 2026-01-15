"""SSO views for StudySphere integration."""
from __future__ import annotations

import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from .services import (
    SSOServiceError,
    build_sso_dispatch_url,
    build_sso_login_url,
    generate_ticket_by_logincode,
    verify_ticket,
)

logger = logging.getLogger(__name__)


def sso_callback(request: HttpRequest) -> HttpResponse:
    ticket = request.GET.get("ticket")
    if not ticket:
        messages.error(request, "SSOチケットが見つかりませんでした。")
        return redirect(settings.LOGIN_URL)

    try:
        sso_data = verify_ticket(ticket)
        user = authenticate(request, sso_data=sso_data)
        if not user:
            messages.error(request, "SSOログインに失敗しました。")
            return redirect(settings.LOGIN_URL)
        login(request, user)
        logger.info("SSO login successful for user_id=%s", sso_data.get("user_id"))
        return redirect(settings.LOGIN_REDIRECT_URL)
    except SSOServiceError as exc:
        logger.warning("SSO callback failed: %s", exc)
        messages.error(request, "SSOログインに失敗しました。")
        return redirect(settings.LOGIN_URL)


def sso_login(request: HttpRequest) -> HttpResponse:
    try:
        if not request.user.is_authenticated:
            messages.error(request, "ログインが必要です。")
            return redirect(settings.LOGIN_URL)
        login_code = getattr(request.user, "studysphere_login_code", None)
        if not login_code:
            messages.error(request, "StudySphereのログインコードが未登録です。")
            return redirect(settings.LOGIN_URL)
        ticket = generate_ticket_by_logincode(login_code, "studysphere", context="portal_click")
        return redirect(build_sso_login_url(ticket))
    except SSOServiceError as exc:
        logger.warning("SSO login redirect failed: %s", exc)
        messages.error(request, "SSOログインに失敗しました。")
        return redirect(settings.LOGIN_URL)


def sso_dispatch(request: HttpRequest, target_system: str) -> HttpResponse:
    try:
        if not request.user.is_authenticated:
            messages.error(request, "ログインが必要です。")
            return redirect(settings.LOGIN_URL)
        login_code = getattr(request.user, "studysphere_login_code", None)
        if not login_code:
            messages.error(request, "StudySphereのログインコードが未登録です。")
            return redirect(settings.LOGIN_URL)
        ticket = generate_ticket_by_logincode(login_code, target_system)
        safe_target = quote(target_system, safe="")
        return redirect(build_sso_dispatch_url(ticket, safe_target))
    except SSOServiceError as exc:
        logger.warning("SSO dispatch failed: %s", exc)
        messages.error(request, "SSO連携に失敗しました。")
        return redirect(settings.LOGIN_URL)
