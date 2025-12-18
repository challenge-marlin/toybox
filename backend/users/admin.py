"""
Users app admin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import UserRegistration, UserMeta, UserCard

User = get_user_model()

# CustomAdminSiteを使用（toybox.urlsで設定済み）
# admin.siteは既にCustomAdminSiteに置き換えられている


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """ユーザー管理 - ユーザー情報の閲覧・編集・削除ができます。"""
    list_display = ['email', 'display_id', 'role', 'is_suspended', 'warning_count', 'is_active', 'is_staff', 'is_superuser']
    list_filter = ['role', 'groups', 'is_suspended', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'display_id', 'old_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['email']
    list_editable = ['role', 'is_staff', 'is_superuser', 'is_active']  # 一覧画面で直接編集可能に（ロールも含む）
    actions = ['issue_warning', 'suspend_account', 'unsuspend_account', 'ban_account']
    filter_horizontal = ('groups', 'user_permissions')
    
    fieldsets = (
        ('認証情報', {
            'fields': ('email', 'password'),
            'description': 'ユーザーのログインに使用するメールアドレスとパスワードを設定します。'
        }),
        ('プロフィール情報', {
            'fields': ('display_id', 'role', 'avatar_url'),
            'description': 'ユーザーの表示名、役割、アバター画像を設定します。'
        }),
        ('管理サイトアクセス権限', {
            'fields': ('is_staff', 'is_superuser', 'is_active'),
            'description': 'is_staff: Django管理サイトへのアクセス権限を付与します。is_superuser: すべての権限を付与します（管理者として動作）。is_active: ユーザーを無効化するとログインできなくなります。'
        }),
        ('モデレーション', {
            'fields': ('is_suspended', 'banned_at', 'warning_count', 'warning_notes', 'penalty_type', 'penalty_message'),
            'description': 'ユーザーのアカウント停止、BAN、警告の管理を行います。penalty_messageはユーザーがログイン時に表示されます。'
        }),
        ('権限グループ', {
            'fields': ('groups', 'user_permissions'),
            'description': 'ユーザーに権限グループや個別の権限を割り当てます。'
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': 'アカウントの作成日時と最終更新日時です。'
        }),
        ('ETL追跡', {
            'fields': ('old_id',),
            'description': 'データ移行時の旧IDを記録します。',
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('認証情報', {
            'fields': ('email', 'password1', 'password2'),
            'description': '新規ユーザーを作成する際のメールアドレスとパスワードを入力します。'
        }),
        ('プロフィール情報', {
            'fields': ('display_id', 'role'),
            'description': 'ユーザーの表示IDと役割を設定します。'
        }),
        ('管理サイトアクセス権限', {
            'fields': ('is_staff', 'is_superuser', 'is_active'),
            'description': 'is_staff: 管理サイトへのアクセス権限。is_superuser: すべての権限。is_active: アカウントの有効/無効。'
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """
        Allow assigning permission groups from Django Admin.

        Django's default UserAdmin hides `groups` / `user_permissions` for non-superusers
        to prevent privilege escalation. In ToyBox we allow users with role=ADMIN
        to manage groups/permissions, but still prevent granting is_superuser via UI.
        """
        kwargs = dict(kwargs)

        # Ensure we don't inherit an exclude tuple that makes fields disappear unexpectedly.
        exclude = list(kwargs.get('exclude') or [])

        if not request.user.is_superuser:
            # Keep groups/user_permissions visible for role=ADMIN only.
            if getattr(request.user, 'role', None) == User.Role.ADMIN:
                # Still prevent toggling Django's is_superuser flag from this UI.
                if 'is_superuser' not in exclude:
                    exclude.append('is_superuser')
            else:
                # Non-superusers that are not role=ADMIN: follow secure default.
                for f in ('is_superuser', 'groups', 'user_permissions'):
                    if f not in exclude:
                        exclude.append(f)

        kwargs['exclude'] = exclude
        return super().get_form(request, obj, **kwargs)
    
    def issue_warning(self, request, queryset):
        """警告を発行します。"""
        from adminpanel.models import AdminAuditLog
        
        warning_message = """ユーザーに規約違反があったため、ペナルティが課せられます。

ご利用規約に違反する行為が確認されました。今後同様の行為を繰り返す場合、アカウント停止やBAN（アカウント削除）などの追加のペナルティが適用される可能性があります。

ご利用規約を再度ご確認いただき、適切な利用をお願いいたします。"""
        
        count = 0
        for user in queryset:
            user.warning_count += 1
            user.penalty_type = 'WARNING'
            user.penalty_message = warning_message
            user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告発行: {request.user.display_id or request.user.email}".strip()
            user.save()
            
            # 監査ログに記録
            AdminAuditLog.objects.create(
                actor=request.user,
                target_user=user,
                action=AdminAuditLog.Action.WARN,
                payload={'warning_count': user.warning_count}
            )
            count += 1
        
        self.message_user(request, f'{count}名のユーザーに警告を発行しました。', messages.SUCCESS)
    issue_warning.short_description = '選択したユーザーに警告を発行'
    
    def suspend_account(self, request, queryset):
        """アカウント停止処置を行います。"""
        from adminpanel.models import AdminAuditLog
        
        suspend_message = """アカウント停止処置が適用されました。

ご利用規約に違反する行為が確認されたため、アカウントを停止いたします。

アカウント停止期間中は、サービスをご利用いただけません。
停止期間が終了するまでお待ちください。

ご不明な点がございましたら、サポートまでお問い合わせください。"""
        
        count = 0
        for user in queryset:
            user.is_suspended = True
            user.penalty_type = 'SUSPEND'
            user.penalty_message = suspend_message
            user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] アカウント停止: {request.user.display_id or request.user.email}".strip()
            user.save()
            
            # 監査ログに記録
            AdminAuditLog.objects.create(
                actor=request.user,
                target_user=user,
                action=AdminAuditLog.Action.SUSPEND,
                payload={}
            )
            count += 1
        
        self.message_user(request, f'{count}名のユーザーをアカウント停止にしました。', messages.SUCCESS)
    suspend_account.short_description = '選択したユーザーをアカウント停止にする'
    
    def unsuspend_account(self, request, queryset):
        """アカウント停止を解除します。"""
        from adminpanel.models import AdminAuditLog
        
        count = 0
        for user in queryset:
            if user.is_suspended:
                user.is_suspended = False
                # アカウント停止に関連するペナルティメッセージをクリア
                if user.penalty_type == 'SUSPEND':
                    user.penalty_type = None
                    user.penalty_message = None
                user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] アカウント停止解除: {request.user.display_id or request.user.email}".strip()
                user.save()
                
                # 監査ログに記録
                AdminAuditLog.objects.create(
                    actor=request.user,
                    target_user=user,
                    action=AdminAuditLog.Action.UNSUSPEND,
                    payload={}
                )
                count += 1
        
        if count > 0:
            self.message_user(request, f'{count}名のユーザーのアカウント停止を解除しました。', messages.SUCCESS)
        else:
            self.message_user(request, 'アカウント停止されているユーザーが選択されていません。', messages.WARNING)
    unsuspend_account.short_description = '選択したユーザーのアカウント停止を解除'
    
    def ban_account(self, request, queryset):
        """BAN（アカウント削除）処置を行います。"""
        from adminpanel.models import AdminAuditLog
        
        ban_message = """BAN（アカウント削除）処置が適用されました。

重大なご利用規約違反が確認されたため、アカウントを削除（BAN）いたします。

この処置により、今後当サービスをご利用いただくことはできません。

ご不明な点がございましたら、サポートまでお問い合わせください。"""
        
        count = 0
        for user in queryset:
            user.is_suspended = True
            user.banned_at = timezone.now()
            user.is_active = False
            user.penalty_type = 'BAN'
            user.penalty_message = ban_message
            user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] BAN（アカウント削除）: {request.user.display_id or request.user.email}".strip()
            user.save()
            
            # 監査ログに記録
            AdminAuditLog.objects.create(
                actor=request.user,
                target_user=user,
                action=AdminAuditLog.Action.BAN,
                payload={}
            )
            count += 1
        
        self.message_user(request, f'{count}名のユーザーをBAN（アカウント削除）にしました。', messages.SUCCESS)
    ban_account.short_description = '選択したユーザーをBAN（アカウント削除）にする'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """ユーザー詳細編集ページにカスタムアクションボタンを追加します。"""
        # カスタムアクションの処理
        if request.method == 'POST' and '_execute_warning' in request.POST:
            return self._execute_warning_action(request, object_id)
        elif request.method == 'POST' and '_execute_suspend' in request.POST:
            return self._execute_suspend_action(request, object_id)
        elif request.method == 'POST' and '_execute_unsuspend' in request.POST:
            return self._execute_unsuspend_action(request, object_id)
        elif request.method == 'POST' and '_execute_ban' in request.POST:
            return self._execute_ban_action(request, object_id)
        
        # 通常のchange_viewを呼び出す
        extra_context = extra_context or {}
        extra_context['show_action_buttons'] = True
        # ユーザーが停止されているかどうかをテンプレートに渡す
        try:
            user = User.objects.get(pk=object_id)
            extra_context['is_suspended'] = user.is_suspended
        except User.DoesNotExist:
            extra_context['is_suspended'] = False
        return super().change_view(request, object_id, form_url, extra_context)
    
    def _execute_warning_action(self, request, object_id):
        """警告を発行します。"""
        from adminpanel.models import AdminAuditLog
        
        try:
            user = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            self.message_user(request, 'ユーザーが見つかりません。', messages.ERROR)
            return redirect('admin:users_user_changelist')
        
        warning_message = """ユーザーに規約違反があったため、ペナルティが課せられます。

ご利用規約に違反する行為が確認されました。今後同様の行為を繰り返す場合、アカウント停止やBAN（アカウント削除）などの追加のペナルティが適用される可能性があります。

ご利用規約を再度ご確認いただき、適切な利用をお願いいたします。"""
        
        user.warning_count += 1
        user.penalty_type = 'WARNING'
        user.penalty_message = warning_message
        user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] 警告発行: {request.user.display_id or request.user.email}".strip()
        user.save()
        
        # 監査ログに記録
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.WARN,
            payload={'warning_count': user.warning_count}
        )
        
        self.message_user(request, f'{user.display_id}に警告を発行しました。', messages.SUCCESS)
        return redirect('admin:users_user_change', object_id)
    
    def _execute_suspend_action(self, request, object_id):
        """アカウント停止処置を行います。"""
        from adminpanel.models import AdminAuditLog
        
        try:
            user = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            self.message_user(request, 'ユーザーが見つかりません。', messages.ERROR)
            return redirect('admin:users_user_changelist')
        
        suspend_message = """アカウント停止処置が適用されました。

ご利用規約に違反する行為が確認されたため、アカウントを停止いたします。

アカウント停止期間中は、サービスをご利用いただけません。
停止期間が終了するまでお待ちください。

ご不明な点がございましたら、サポートまでお問い合わせください。"""
        
        user.is_suspended = True
        user.penalty_type = 'SUSPEND'
        user.penalty_message = suspend_message
        user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] アカウント停止: {request.user.display_id or request.user.email}".strip()
        user.save()
        
        # 監査ログに記録
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.SUSPEND,
            payload={}
        )
        
        self.message_user(request, f'{user.display_id}をアカウント停止にしました。', messages.SUCCESS)
        return redirect('admin:users_user_change', object_id)
    
    def _execute_unsuspend_action(self, request, object_id):
        """アカウント停止を解除します。"""
        from adminpanel.models import AdminAuditLog
        
        try:
            user = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            self.message_user(request, 'ユーザーが見つかりません。', messages.ERROR)
            return redirect('admin:users_user_changelist')
        
        if not user.is_suspended:
            self.message_user(request, 'このユーザーはアカウント停止されていません。', messages.WARNING)
            return redirect('admin:users_user_change', object_id)
        
        user.is_suspended = False
        # アカウント停止に関連するペナルティメッセージをクリア
        if user.penalty_type == 'SUSPEND':
            user.penalty_type = None
            user.penalty_message = None
        user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] アカウント停止解除: {request.user.display_id or request.user.email}".strip()
        user.save()
        
        # 監査ログに記録
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.UNSUSPEND,
            payload={}
        )
        
        self.message_user(request, f'{user.display_id}のアカウント停止を解除しました。', messages.SUCCESS)
        return redirect('admin:users_user_change', object_id)
    
    def _execute_ban_action(self, request, object_id):
        """BAN（アカウント削除）処置を行います。"""
        from adminpanel.models import AdminAuditLog
        
        try:
            user = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            self.message_user(request, 'ユーザーが見つかりません。', messages.ERROR)
            return redirect('admin:users_user_changelist')
        
        ban_message = """BAN（アカウント削除）処置が適用されました。

重大なご利用規約違反が確認されたため、アカウントを削除（BAN）いたします。

この処置により、今後当サービスをご利用いただくことはできません。

ご不明な点がございましたら、サポートまでお問い合わせください。"""
        
        user.is_suspended = True
        user.banned_at = timezone.now()
        user.is_active = False
        user.penalty_type = 'BAN'
        user.penalty_message = ban_message
        user.warning_notes = f"{user.warning_notes or ''}\n[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] BAN（アカウント削除）: {request.user.display_id or request.user.email}".strip()
        user.save()
        
        # 監査ログに記録
        AdminAuditLog.objects.create(
            actor=request.user,
            target_user=user,
            action=AdminAuditLog.Action.BAN,
            payload={}
        )
        
        self.message_user(request, f'{user.display_id}をBAN（アカウント削除）にしました。', messages.SUCCESS)
        return redirect('admin:users_user_change', object_id)


@admin.register(UserRegistration)
class UserRegistrationAdmin(admin.ModelAdmin):
    """ユーザー登録情報管理 - ユーザーの追加登録情報（住所、年齢層、電話番号など）を管理します。"""
    list_display = ['user', 'age_group', 'created_at']
    search_fields = ['user__email', 'user__display_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('ユーザー情報', {
            'fields': ('user',),
            'description': '登録情報を紐付けるユーザーを選択します。'
        }),
        ('登録情報', {
            'fields': ('address', 'age_group', 'phone'),
            'description': 'ユーザーの住所、年齢層、電話番号などの追加情報を入力します。'
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': '登録情報の作成日時と最終更新日時です。'
        }),
    )


@admin.register(UserMeta)
class UserMetaAdmin(admin.ModelAdmin):
    """ユーザーメタ情報管理 - ユーザーの称号、プロフィール情報、抽選ボーナスなどを管理します。"""
    list_display = ['user', 'display_name', 'active_title', 'title_color', 'expires_at', 'lottery_bonus_count']
    search_fields = ['user__email', 'user__display_id', 'old_id']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['expires_at']
    fieldsets = (
        ('ユーザー情報', {
            'fields': ('user',),
            'description': 'メタ情報を紐付けるユーザーを選択します。'
        }),
        ('プロフィール情報', {
            'fields': ('display_name', 'bio', 'header_url'),
            'description': 'ユーザーの表示名、自己紹介、ヘッダー画像を設定します。'
        }),
        ('称号情報', {
            'fields': ('active_title', 'title_color', 'expires_at'),
            'description': 'ユーザーに付与された称号とその有効期限を管理します。'
        }),
        ('抽選ボーナス', {
            'fields': ('lottery_bonus_count',),
            'description': 'ユーザーが持つ抽選ボーナス回数を管理します。'
        }),
        ('通知', {
            'fields': ('notifications',),
            'description': 'ユーザーへの通知情報を管理します。',
            'classes': ('collapse',)
        }),
        ('日時情報', {
            'fields': ('created_at', 'updated_at'),
            'description': 'メタ情報の作成日時と最終更新日時です。'
        }),
    )


@admin.register(UserCard)
class UserCardAdmin(admin.ModelAdmin):
    """ユーザーカード管理 - ユーザーが獲得したカードの一覧を管理します。"""
    list_display = ['user', 'card', 'obtained_at']
    search_fields = ['user__email', 'user__display_id', 'card__code']
    list_filter = ['obtained_at', 'card__rarity']
    readonly_fields = ['obtained_at']
    fieldsets = (
        ('ユーザー情報', {
            'fields': ('user',),
            'description': 'カードを獲得したユーザーを選択します。'
        }),
        ('カード情報', {
            'fields': ('card', 'obtained_at'),
            'description': '獲得したカードと獲得日時を表示します。'
        }),
    )
