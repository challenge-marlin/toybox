"""SSO views for StudySphere integration."""
from __future__ import annotations

import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .services import (
    SSOServiceError,
    build_sso_dispatch_url,
    build_sso_login_url,
    build_sso_return_url,
    generate_ticket_by_logincode,
    verify_ticket,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def sso_callback(request: HttpRequest) -> HttpResponse:
    ticket = request.GET.get("ticket")
    if not ticket:
        logger.warning("SSO callback missing ticket")
        try:
            return redirect(build_sso_return_url())
        except SSOServiceError:
            messages.error(request, "SSOチケットが見つかりませんでした。")
            return redirect(settings.LOGIN_URL)

    # チケットはワンタイムのため、ここでは検証せずログイン画面で検証する
    logger.info("SSO callback received ticket, redirecting to login for verification")
    return redirect(f"/login/?ticket={ticket}")


@csrf_exempt
def sso_login(request: HttpRequest) -> HttpResponse:
    """
    SSOログインエンドポイント
    - GET: TOYBOXにログイン済みのユーザーがStudySphereにリダイレクト（既存の動作）
    - POST: StudySphere側からのPOSTリクエストでチケットを受け取り、検証してログイン/登録
    """
    # POSTリクエストの場合（StudySphere側からのリクエスト）
    if request.method == 'POST':
        # クエリパラメータからチケットを取得
        ticket = request.GET.get("ticket") or request.POST.get("ticket")
        
        if not ticket:
            logger.warning("SSO login POST missing ticket")
            messages.error(request, "SSOチケットが見つかりませんでした。")
            return redirect(settings.LOGIN_URL)
        
        try:
            logger.info("SSO login POST - verifying ticket: %s", ticket[:20] + "..." if len(ticket) > 20 else ticket)
            
            # チケットを検証（StudySphere側のSSO APIを呼び出し）
            result = verify_ticket(ticket)
            
            if not result.get("valid"):
                logger.warning("SSO login POST invalid ticket: %s", result.get("error"))
                messages.error(request, "SSOチケットが無効です。")
                # チケットがある場合はサインアップ画面にリダイレクト（エラーメッセージを表示）
                return redirect(f"/signup/?ticket={ticket}")
            
            sso_data = result.get("data") or {}
            studysphere_user_id = sso_data.get("user_id")
            
            if not studysphere_user_id:
                logger.warning("SSO login POST missing user_id")
                messages.error(request, "StudySphereユーザーIDが取得できませんでした。")
                return redirect(f"/signup/?ticket={ticket}")
            
            logger.info("SSO login POST verified - user_id: %s, username: %s", 
                       studysphere_user_id, sso_data.get("username"))
            
            # アカウント存在チェック（studysphere_user_idまたはstudysphere_login_codeで検索）
            user = None
            studysphere_login_code = sso_data.get("login_code") or sso_data.get("username") or ""
            try:
                # まずstudysphere_user_idで検索
                user = User.objects.get(studysphere_user_id=studysphere_user_id)
                logger.info("SSO login POST - user found by studysphere_user_id: %s", studysphere_user_id)
            except User.DoesNotExist:
                # studysphere_user_idで見つからない場合、studysphere_login_codeで検索
                if studysphere_login_code:
                    try:
                        user = User.objects.get(studysphere_login_code=studysphere_login_code)
                        logger.info("SSO login POST - user found by studysphere_login_code")
                    except User.DoesNotExist:
                        pass
            
            if user:
                # ID 2対応: 既に同一ユーザーでログイン済みの場合はそのままマイページへ
                if request.user.is_authenticated and request.user.id == user.id:
                    logger.info("SSO login POST - already logged in as same user (user_id=%s), redirecting to home", user.id)
                    return redirect(settings.LOGIN_REDIRECT_URL)
                
                # ID 3対応: 別のユーザーでログイン済みの場合は警告ログを出してログアウト→再ログイン
                if request.user.is_authenticated and request.user.id != user.id:
                    logger.warning("SSO login POST - switching user from %s to %s", request.user.id, user.id)
                    from django.contrib.auth import logout
                    logout(request)
                
                # StudySphere情報を更新
                updated = False
                if user.studysphere_user_id != studysphere_user_id:
                    user.studysphere_user_id = studysphere_user_id
                    updated = True
                if studysphere_login_code and user.studysphere_login_code != studysphere_login_code:
                    user.studysphere_login_code = studysphere_login_code
                    updated = True
                if updated:
                    user.save(update_fields=["studysphere_user_id", "studysphere_login_code"])
                
                # アカウントあり → 直接ログイン（authenticateを使わない＝新規ユーザー作成を防ぐ）
                logger.info("SSO login POST - account found, logging in: %s", user.display_id)
                user.backend = 'sso_integration.backends.StudySphereBackend'
                login(request, user)
                logger.info("SSO login POST successful for user_id=%s", studysphere_user_id)
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                # ID 4対応: アカウントなし → サインアップ画面にチケット付きでリダイレクト
                # 既にログイン済みの場合は一旦ログアウト
                if request.user.is_authenticated:
                    logger.info("SSO login POST - user is logged in, logging out before signup (current_user_id=%s, new_studysphere_user_id=%s)", 
                               request.user.id, studysphere_user_id)
                    from django.contrib.auth import logout
                    logout(request)
                logger.info("SSO login POST - account not found, redirecting to signup with ticket (user_id=%s)", studysphere_user_id)
                return redirect(f"/signup/?ticket={ticket}")
                
        except SSOServiceError as exc:
            logger.error("SSO login POST SSOServiceError: %s", exc, exc_info=True)
            messages.error(request, "SSOログインに失敗しました。")
            # チケットがある場合はサインアップ画面にリダイレクト
            ticket = request.GET.get("ticket") or request.POST.get("ticket")
            if ticket:
                return redirect(f"/signup/?ticket={ticket}")
            return redirect(settings.LOGIN_URL)
        except Exception as exc:
            logger.exception("SSO login POST unexpected error: %s", exc)
            messages.error(request, "SSOログイン処理中にエラーが発生しました。")
            # チケットがある場合はサインアップ画面にリダイレクト
            ticket = request.GET.get("ticket") or request.POST.get("ticket")
            if ticket:
                return redirect(f"/signup/?ticket={ticket}")
            return redirect(settings.LOGIN_URL)
    
    # GETリクエストの場合（既存の動作：TOYBOXからStudySphereへのリダイレクト）
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
        logger.error("SSO login redirect SSOServiceError: %s", exc, exc_info=True)
        messages.error(request, "SSOログインに失敗しました。")
        return redirect(settings.LOGIN_URL)
    except Exception as exc:
        logger.exception("SSO login redirect unexpected error: %s", exc)
        messages.error(request, "SSOログイン処理中にエラーが発生しました。")
        return redirect(settings.LOGIN_URL)


def sso_dispatch(request: HttpRequest, target_system: str) -> HttpResponse:
    """
    SSOディスパッチエンドポイント
    TOYBOXにログイン済みのユーザーを他のシステム（StudySphereなど）にリダイレクト
    """
    from django.shortcuts import render
    
    # GETリクエストでredirectパラメータがない場合はローディングページを表示
    if request.method == 'GET' and not request.GET.get('redirect'):
        # 認証チェック
        if not request.user.is_authenticated:
            messages.error(request, "ログインが必要です。")
            return redirect(settings.LOGIN_URL)
        
        # ローディングページを表示（JavaScriptで自動リダイレクト）
        return render(request, 'frontend/sso_dispatch.html', {
            'target_system': target_system
        })
    
    # POSTリクエストまたはticketパラメータがある場合はリダイレクト処理
    # 認証チェック
    if not request.user.is_authenticated:
        messages.error(request, "ログインが必要です。")
        return redirect(settings.LOGIN_URL)
    
    try:
        login_code = getattr(request.user, "studysphere_login_code", None)
        if not login_code:
            # login_codeがない場合は、studysphere_user_idがあるかチェック
            studysphere_user_id = getattr(request.user, "studysphere_user_id", None)
            if studysphere_user_id:
                # studysphere_user_idはあるがlogin_codeがない場合（新規連携直後など）
                # StudySphereダッシュボードに直接リダイレクト
                logger.warning(f"User {request.user.id} has studysphere_user_id but no login_code, redirecting to StudySphere dashboard")
                return redirect("https://studysphere.ayatori-inc.co.jp/student/dashboard")
            else:
                # 未連携ユーザーの場合もダッシュボードへ（StudySphere側でログイン処理される）
                logger.info(f"User {request.user.id} is not linked to StudySphere, redirecting to dashboard")
                return redirect("https://studysphere.ayatori-inc.co.jp/student/dashboard")
        
        ticket = generate_ticket_by_logincode(login_code, target_system)
        safe_target = quote(target_system, safe="")
        # StudySphereの場合はダッシュボードページにリダイレクト
        return_url = "https://studysphere.ayatori-inc.co.jp/student/dashboard" if target_system == "studysphere" else None
        return redirect(build_sso_dispatch_url(ticket, safe_target, return_url))
    except SSOServiceError as exc:
        logger.error("SSO dispatch SSOServiceError: %s", exc, exc_info=True)
        messages.error(request, "SSO連携に失敗しました。StudySphereダッシュボードにリダイレクトします。")
        return redirect("https://studysphere.ayatori-inc.co.jp/student/dashboard")
    except Exception as exc:
        logger.exception("SSO dispatch unexpected error: %s", exc)
        messages.error(request, "SSO連携処理中にエラーが発生しました。StudySphereダッシュボードにリダイレクトします。")
        return redirect("https://studysphere.ayatori-inc.co.jp/student/dashboard")


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def sso_verify_and_check(request: HttpRequest) -> JsonResponse:
    """
    チケット検証 + アカウント存在チェックAPI
    
    Request (POST): { "ticket": "xxx" }
    Request (GET): /sso/verify-and-check/?ticket=xxx
    Response:
    - アカウントあり: { "has_account": true, "access": "...", "refresh": "...", "user": {...}, "sso_data": {...} }
    - アカウントなし: { "has_account": false, "sso_data": {...} }
    - エラー: { "error": "..." }
    """
    ticket = request.query_params.get("ticket") or request.data.get("ticket")
    if not ticket:
        return JsonResponse({"error": "チケットが指定されていません"}, status=400)
    
    try:
        # チケット検証
        result = verify_ticket(ticket)
        if not result.get("valid"):
            error_msg = result.get("error") or "無効なチケットです"
            return JsonResponse({"error": error_msg}, status=400)
        
        sso_data = result.get("data") or {}
        studysphere_user_id = sso_data.get("user_id")
        
        if not studysphere_user_id:
            return JsonResponse({"error": "StudySphereユーザーIDが取得できませんでした"}, status=400)
        
        # SSO情報を準備（login_codeがない場合はusernameを使用）
        studysphere_login_code = sso_data.get("login_code") or sso_data.get("username") or ""
        studysphere_username = sso_data.get("username") or ""
        sso_info = {
            "studysphere_user_id": studysphere_user_id,
            "studysphere_login_code": studysphere_login_code,
            "studysphere_username": studysphere_username,
        }
        
        # アカウント存在チェック（studysphere_user_idまたはstudysphere_login_codeで検索）
        user = None
        try:
            # まずstudysphere_user_idで検索
            user = User.objects.get(studysphere_user_id=studysphere_user_id)
            logger.info(f"User found by studysphere_user_id: {studysphere_user_id}")
        except User.DoesNotExist:
            # studysphere_user_idで見つからない場合、studysphere_login_codeで検索
            if studysphere_login_code:
                try:
                    user = User.objects.get(studysphere_login_code=studysphere_login_code)
                    logger.info(f"User found by studysphere_login_code: {studysphere_login_code[:20]}...")
                except User.DoesNotExist:
                    logger.info(f"User not found by studysphere_user_id ({studysphere_user_id}) or studysphere_login_code")
                    pass
        
        if user:
            # アカウントあり → セッションログイン（authenticateは呼ばず直接ログイン）
            # StudySphere情報を更新
            updated = False
            if user.studysphere_user_id != studysphere_user_id:
                user.studysphere_user_id = studysphere_user_id
                updated = True
            if studysphere_login_code and user.studysphere_login_code != studysphere_login_code:
                user.studysphere_login_code = studysphere_login_code
                updated = True
            if updated:
                user.save(update_fields=["studysphere_user_id", "studysphere_login_code"])
                logger.info(f"Updated StudySphere info for user {user.id}")
            
            # 直接ログイン（authenticateを使わない＝新規ユーザー作成を防ぐ）
            user.backend = 'sso_integration.backends.StudySphereBackend'
            login(request, user)
            refresh = RefreshToken.for_user(user)
            logger.info(f"SSO verify-and-check: User {user.id} logged in successfully")
            return JsonResponse({
                "has_account": True,
                "logged_in": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "username": user.display_id,
                    "display_name": getattr(user, 'display_name', '') or user.display_id,
                    "role": user.role,
                },
                "sso_data": sso_info
            })
        else:
            # アカウントなし → 登録画面で使うSSO情報を返す
            logger.info(f"No account found for studysphere_user_id={studysphere_user_id}, login_code={studysphere_login_code[:20] if studysphere_login_code else 'None'}...")
            return JsonResponse({
                "has_account": False,
                "sso_data": sso_info
            })
    
    except SSOServiceError as exc:
        logger.error("SSO verify and check SSOServiceError: %s", exc, exc_info=True)
        return JsonResponse({"error": "SSO検証に失敗しました"}, status=500)
    except Exception as exc:
        logger.exception("SSO verify and check unexpected error: %s", exc)
        return JsonResponse({"error": "SSO検証処理中にエラーが発生しました"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def sso_login_with_ticket(request: HttpRequest) -> JsonResponse:
    """
    SSO経由のログインAPI（IDとチケットでログイン）
    
    Request: { "display_id": "xxx", "ticket": "xxx" }
    Response:
    - 成功: { "access": "...", "refresh": "...", "user": {...} }
    - エラー: { "error": "..." }
    """
    display_id = request.data.get("display_id", "").strip()
    ticket = request.data.get("ticket")
    
    if not display_id:
        return JsonResponse({"error": "IDが指定されていません"}, status=400)
    if not ticket:
        return JsonResponse({"error": "チケットが指定されていません"}, status=400)
    
    try:
        # チケット検証
        result = verify_ticket(ticket)
        if not result.get("valid"):
            error_msg = result.get("error") or "無効なチケットです"
            return JsonResponse({"error": error_msg}, status=400)
        
        sso_data = result.get("data") or {}
        studysphere_user_id = sso_data.get("user_id")
        
        if not studysphere_user_id:
            return JsonResponse({"error": "StudySphereユーザーIDが取得できませんでした"}, status=400)
        
        # ユーザーを検索（StudySphere user_idまたはdisplay_idで）
        try:
            user = User.objects.get(studysphere_user_id=studysphere_user_id)
            # display_idが一致するか確認
            if user.display_id != display_id:
                return JsonResponse({"error": "IDが一致しません"}, status=400)
        except User.DoesNotExist:
            return JsonResponse({"error": "アカウントが見つかりませんでした"}, status=404)
        
        # SSO認証でログイン
        user = authenticate(request, sso_data=sso_data)
        if not user:
            return JsonResponse({"error": "SSO認証に失敗しました"}, status=400)
        
        # トークン発行
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "username": user.display_id,
                "display_name": getattr(user, 'display_name', '') or user.display_id,
                "role": user.role,
            }
        })
    
    except SSOServiceError as exc:
        logger.error("SSO login with ticket SSOServiceError: %s", exc, exc_info=True)
        return JsonResponse({"error": "SSO検証に失敗しました"}, status=500)
    except Exception as exc:
        logger.exception("SSO login with ticket unexpected error: %s", exc)
        return JsonResponse({"error": "SSOログイン処理中にエラーが発生しました"}, status=500)
