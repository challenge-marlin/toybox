"""
Frontend app views - Template views and API views.
"""
import logging
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from .models import Announcement
from .email_utils import send_form_email, validate_email_config

logger = logging.getLogger(__name__)


# Template views
def index(request):
    """Home page."""
    return render(request, 'frontend/index.html')


def feed(request):
    """Feed page."""
    from django.contrib.auth import get_user_model
    from django.shortcuts import redirect
    from users.models import UserMeta
    
    User = get_user_model()
    
    # ログインしているかチェック
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    # 課金ユーザーで利用規約未同意の場合は利用規約同意ページにリダイレクト
    if request.user.role == User.Role.PAID_USER:
        try:
            meta = request.user.meta
            if not meta.terms_agreed_at:
                return redirect('/terms/agree/')
        except UserMeta.DoesNotExist:
            # UserMetaが存在しない場合も利用規約未同意とみなす
            return redirect('/terms/agree/')
    
    return render(request, 'frontend/feed.html')


def login_page(request):
    """Login page."""
    return render(request, 'frontend/login.html')


def signup_page(request):
    """Signup page."""
    return render(request, 'frontend/signup.html')


def me(request):
    """My page."""
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.shortcuts import redirect
    from users.models import UserMeta
    
    User = get_user_model()
    
    # ログインしているかチェック
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    # 一般ユーザー（FREE_USER）はマイページにアクセスできない
    if request.user.role == User.Role.FREE_USER:
        return redirect('/upgrade/')
    
    # 課金ユーザーで利用規約未同意の場合は利用規約同意ページにリダイレクト
    if request.user.role == User.Role.PAID_USER:
        try:
            meta = request.user.meta
            if not meta.terms_agreed_at:
                return redirect('/terms/agree/')
        except UserMeta.DoesNotExist:
            # UserMetaが存在しない場合も利用規約未同意とみなす
            return redirect('/terms/agree/')
    
    discord_invite_code = getattr(settings, 'DISCORD_INVITE_CODE', '')
    return render(request, 'frontend/me.html', {
        'DISCORD_INVITE_CODE': discord_invite_code
    })


def upgrade(request):
    """一般ユーザー向けの課金問い合わせページ。"""
    # JWTトークン認証を使用しているため、サーバー側での認証チェックは行わない
    # フロントエンド側でJWTトークンを使ってロールチェックを行う
    return render(request, 'frontend/upgrade.html')


def lottery(request):
    """Lottery page."""
    from django.contrib.auth import get_user_model
    from django.shortcuts import redirect
    from users.models import UserMeta
    
    User = get_user_model()
    
    # ログインしているかチェック
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    # 課金ユーザーで利用規約未同意の場合は利用規約同意ページにリダイレクト
    if request.user.role == User.Role.PAID_USER:
        try:
            meta = request.user.meta
            if not meta.terms_agreed_at:
                return redirect('/terms/agree/')
        except UserMeta.DoesNotExist:
            # UserMetaが存在しない場合も利用規約未同意とみなす
            return redirect('/terms/agree/')
    
    return render(request, 'frontend/lottery.html')


def collection(request):
    """Collection page."""
    from django.contrib.auth import get_user_model
    from django.shortcuts import redirect
    from users.models import UserMeta
    
    User = get_user_model()
    
    # ログインしているかチェック
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    # 課金ユーザーで利用規約未同意の場合は利用規約同意ページにリダイレクト
    if request.user.role == User.Role.PAID_USER:
        try:
            meta = request.user.meta
            if not meta.terms_agreed_at:
                return redirect('/terms/agree/')
        except UserMeta.DoesNotExist:
            # UserMetaが存在しない場合も利用規約未同意とみなす
            return redirect('/terms/agree/')
    
    return render(request, 'frontend/collection.html')


def profile(request):
    """Profile page."""
    from django.contrib.auth import get_user_model
    from django.shortcuts import redirect
    from users.models import UserMeta
    
    User = get_user_model()
    
    # ログインしているかチェック
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    # 課金ユーザーで利用規約未同意の場合は利用規約同意ページにリダイレクト
    if request.user.role == User.Role.PAID_USER:
        try:
            meta = request.user.meta
            if not meta.terms_agreed_at:
                return redirect('/terms/agree/')
        except UserMeta.DoesNotExist:
            # UserMetaが存在しない場合も利用規約未同意とみなす
            return redirect('/terms/agree/')
    
    return render(request, 'frontend/profile.html')


def profile_view(request):
    """Profile view page."""
    return render(request, 'frontend/profile_view.html')


def announcements_list(request):
    """Announcements list page."""
    from datetime import datetime, timedelta
    from django.utils import timezone
    from .models import Announcement
    
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-created_at')
    
    # 3日以内のお知らせにNEWマークを付ける
    three_days_ago = timezone.now() - timedelta(days=3)
    announcements_with_new = []
    for announcement in announcements:
        is_new = announcement.created_at >= three_days_ago
        announcements_with_new.append({
            'announcement': announcement,
            'is_new': is_new
        })
    
    return render(request, 'frontend/announcements_list.html', {
        'announcements_with_new': announcements_with_new
    })


def announcement_detail(request, announcement_id):
    """Announcement detail page."""
    from .models import Announcement
    try:
        announcement = Announcement.objects.get(id=announcement_id, is_active=True)
    except Announcement.DoesNotExist:
        from django.http import Http404
        raise Http404("お知らせが見つかりません")
    
    return render(request, 'frontend/announcement_detail.html', {
        'announcement': announcement
    })


def terms(request):
    """Terms of use page."""
    return render(request, 'frontend/terms.html')


def terms_agree(request):
    """Terms agreement page for paid users (first time only)."""
    from django.contrib.auth import get_user_model
    from django.shortcuts import redirect
    from users.models import UserMeta
    
    User = get_user_model()
    
    # ログインしているかチェック
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    # 課金ユーザー以外は通常の利用規約ページにリダイレクト
    if request.user.role != User.Role.PAID_USER:
        return redirect('/terms/')
    
    # 既に同意済みの場合は通常の利用規約ページにリダイレクト
    try:
        meta = request.user.meta
        if meta.terms_agreed_at:
            return redirect('/terms/')
    except UserMeta.DoesNotExist:
        # UserMetaが存在しない場合は同意ページを表示
        pass
    
    return render(request, 'frontend/terms_agree.html')


def inquiry(request):
    """Inquiry/Report form page."""
    return render(request, 'frontend/inquiry.html')


def derivative_guidelines(request):
    """Derivative works guidelines page."""
    return render(request, 'frontend/derivative_guidelines.html')


def topic_help(request):
    """Topic generation help page."""
    return render(request, 'frontend/topic_help.html')


def tutorial_image(request):
    """Image creation tutorial page."""
    return render(request, 'frontend/tutorials/image.html')


def tutorial_video(request):
    """Video creation tutorial page."""
    return render(request, 'frontend/tutorials/video.html')


def tutorial_game(request):
    """Web game creation tutorial page."""
    return render(request, 'frontend/tutorials/game.html')


def privacy(request):
    """Privacy policy page."""
    return render(request, 'frontend/privacy.html')


def maintenance_preview(request):
    """Maintenance screen preview (always renders the maintenance page)."""
    from .models import SiteMaintenance
    s = SiteMaintenance.get_solo()
    return render(request, 'frontend/maintenance.html', {
        'message': s.message,
        'scheduled_end': s.scheduled_end,
    }, status=503)


# API views
class AnnouncementsView(APIView):
    """Get active announcements."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get active announcements ordered by created_at descending."""
        announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-created_at')[:10]  # 最新10件まで
        
        announcements_data = []
        for announcement in announcements:
            announcements_data.append({
                'id': announcement.id,
                'title': announcement.title,
                'content': announcement.content,
                'created_at': announcement.created_at.isoformat(),
            })
        
        return Response({
            'announcements': announcements_data
        })


class ContactView(APIView):
    """Contact form API endpoint."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Send contact email to AYATORI."""
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        message = request.data.get('message', '').strip()
        
        # Validation
        if not name:
            return Response(
                {'ok': False, 'error': 'お名前は必須です。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not message or len(message) < 5:
            return Response(
                {'ok': False, 'error': '問い合わせ内容は5文字以上で入力してください。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepare email content
        subject = '[ToyBox] 課金についての問い合わせ'
        email_body = f"""お名前: {name}
メールアドレス: {email or '未入力'}
ユーザーID: {request.user.display_id or request.user.email or '不明'}

問い合わせ内容:
{message}
"""
        
        # Validate email configuration
        is_valid, config_error = validate_email_config()
        if not is_valid:
            logger.warning(f'Email configuration error: {config_error}')
            # Continue anyway - email will be logged if console backend
        
        # Send email
        success, error_msg = send_form_email(
            subject=subject,
            body=email_body,
        )
        
        if success:
            return Response({
                'ok': True,
                'message': '問い合わせを送信しました。'
            })
        else:
            # Log error but still return success to user
            # Email content is already logged in send_form_email
            logger.error(f'Contact form email sending failed: {error_msg}')
            return Response({
                'ok': True,
                'message': '問い合わせを送信しました。'
            })


class InquiryView(APIView):
    """Inquiry/Report form API endpoint (for terms violations, bug reports, etc.)."""
    permission_classes = [AllowAny]  # 認証なしで利用可能
    
    def post(self, request):
        """Send inquiry/report email to AYATORI."""
        inquiry_type = request.data.get('type', '').strip()
        game_title = request.data.get('gameTitle', '').strip()
        detail = request.data.get('detail', '').strip()
        contact = request.data.get('contact', '').strip()
        
        # Validation
        if not inquiry_type:
            return Response(
                {'ok': False, 'error': '種別は必須です。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not detail or len(detail) < 10:
            return Response(
                {'ok': False, 'error': '詳細内容は10文字以上で入力してください。'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 種別のラベル
        type_labels = {
            'bug_report': '不具合報告',
            'violation_report': '規約違反の通報',
            'other': 'その他お問い合わせ',
        }
        type_label = type_labels.get(inquiry_type, inquiry_type)
        
        # Prepare email content
        subject = f'[ToyBox] {type_label}'
        email_body = f"""種別: {type_label}
対象ゲーム名: {game_title or '未入力'}
任意連絡先: {contact or '未入力'}
"""
        
        # 認証済みユーザーの場合はユーザー情報を追加
        if request.user.is_authenticated:
            email_body += f"ユーザーID: {request.user.display_id or request.user.email or '不明'}\n"
        else:
            email_body += "ユーザーID: 未ログイン\n"
        
        email_body += f"""
詳細内容:
{detail}
"""
        
        # Validate email configuration
        is_valid, config_error = validate_email_config()
        if not is_valid:
            logger.warning(f'Email configuration error: {config_error}')
            # Continue anyway - email will be logged if console backend
        
        # Send email
        success, error_msg = send_form_email(
            subject=subject,
            body=email_body,
        )
        
        if success:
            return Response({
                'ok': True,
                'message': 'お問い合わせを送信しました。'
            })
        else:
            # Log error but still return success to user
            # Email content is already logged in send_form_email
            logger.error(f'Inquiry form email sending failed: {error_msg}')
            return Response({
                'ok': True,
                'message': 'お問い合わせを送信しました。'
            })