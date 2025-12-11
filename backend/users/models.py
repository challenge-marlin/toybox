"""
Users app models - RDB redesign from MongoDB.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, email=None, password=None, display_id=None, **extra_fields):
        """Create and save a regular user."""
        # Email is optional - if not provided, generate a dummy email
        if email:
            email = self.normalize_email(email)
        elif display_id:
            # Generate a dummy email if display_id is provided
            email = f"{display_id}@toybox.local"
        else:
            raise ValueError('Either email or display_id must be set')
        
        display_id = display_id or (email.split('@')[0] if email else None)
        if not display_id:
            raise ValueError('display_id must be set')
        
        user = self.model(
            email=email,
            display_id=display_id,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('role', User.Role.SUPERUSER)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model."""
    
    class Role(models.TextChoices):
        FREE_USER = 'FREE_USER', '一般ユーザー'
        PAID_USER = 'PAID_USER', '課金ユーザー'
        ADMIN = 'ADMIN', '管理者'
        SUPERUSER = 'SUPERUSER', 'スーパーユーザー'
    
    # Authentication fields
    email = models.EmailField('メールアドレス', unique=True, null=True, blank=True, db_index=True)
    password = models.CharField('パスワード', max_length=128)  # AbstractBaseUser provides this
    
    # Profile fields
    display_id = models.CharField('表示ID', max_length=100, db_index=True)
    role = models.CharField('役割', max_length=20, choices=Role.choices, default=Role.FREE_USER)
    avatar_url = models.URLField('アバターURL', max_length=500, blank=True, null=True)
    
    # Moderation fields
    is_suspended = models.BooleanField('アカウント停止', default=False)
    banned_at = models.DateTimeField('BAN日時', null=True, blank=True)
    warning_count = models.IntegerField('警告回数', default=0)
    warning_notes = models.TextField('警告メモ', blank=True, null=True)
    penalty_message = models.TextField('ペナルティメッセージ', blank=True, null=True, help_text='ユーザーに表示する警告・ペナルティメッセージ')
    penalty_type = models.CharField('ペナルティタイプ', max_length=20, blank=True, null=True, help_text='WARNING: 警告, SUSPEND: アカウント停止, BAN: BAN（アカウント削除）')
    
    # Django admin fields
    is_active = models.BooleanField('アクティブ', default=True, help_text='このユーザーがアクティブかどうか。無効にするとログインできません。')
    is_staff = models.BooleanField('管理サイトアクセス権限', default=False, help_text='このユーザーがDjango管理サイトにアクセスできるかどうか。')
    is_superuser = models.BooleanField('スーパーユーザー', default=False, help_text='このユーザーがすべての権限を持つかどうか。')
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_id']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['display_id']),
            models.Index(fields=['role']),
            models.Index(fields=['is_suspended']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.display_id} ({self.email})'
    
    def get_full_name(self):
        """Return the full name for the user."""
        return self.display_name if hasattr(self, 'meta') and self.meta.display_name else self.display_id
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.display_id


class UserRegistration(models.Model):
    """User registration profile (optional fields)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration')
    
    # Optional profile fields (adjust based on existing requirements)
    address = models.TextField(blank=True, null=True)
    age_group = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Additional fields can be added here
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_registrations'
        verbose_name = 'ユーザー登録情報'
        verbose_name_plural = 'ユーザー登録情報'
    
    def __str__(self):
        return f'{self.user.display_id}の登録情報'


class UserMeta(models.Model):
    """User metadata (title, etc.)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='meta')
    
    # Title information
    active_title = models.CharField(max_length=100, blank=True, null=True)
    title_color = models.CharField(max_length=50, blank=True, null=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Profile fields
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(max_length=1000, blank=True)
    header_url = models.URLField(max_length=500, blank=True, null=True)
    lottery_bonus_count = models.IntegerField(default=0)
    
    # Notifications (JSON array of notification objects)
    notifications = models.JSONField(default=list, blank=True)
    
    # Onboarding (page-specific completion status)
    onboarding_completed = models.JSONField('オンボーディング完了状態', default=dict, blank=True, help_text='各ページごとのオンボーディング完了状態 {"me": false, "collection": false, "profile": false, "feed": false}')
    
    # Terms agreement (for paid users)
    terms_agreed_at = models.DateTimeField('利用規約同意日時', null=True, blank=True, help_text='課金ユーザーが利用規約に同意した日時')
    
    # Discord OAuth integration
    discord_access_token = models.TextField('Discordアクセストークン', blank=True, null=True, help_text='Discord OAuth2アクセストークン（暗号化推奨）')
    discord_refresh_token = models.TextField('Discordリフレッシュトークン', blank=True, null=True, help_text='Discord OAuth2リフレッシュトークン（暗号化推奨）')
    discord_token_expires_at = models.DateTimeField('Discordトークン有効期限', blank=True, null=True, help_text='Discordアクセストークンの有効期限')
    discord_user_id = models.CharField('DiscordユーザーID', max_length=100, blank=True, null=True, db_index=True, help_text='DiscordユーザーID')
    discord_username = models.CharField('Discordユーザー名', max_length=255, blank=True, null=True, help_text='Discordユーザー名（例: username#1234）')
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_meta'
        verbose_name = 'ユーザーメタ情報'
        verbose_name_plural = 'ユーザーメタ情報'
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.user.display_id}のメタ情報'


class UserCard(models.Model):
    """User's card collection."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey('gamification.Card', on_delete=models.CASCADE, related_name='user_cards')
    obtained_at = models.DateTimeField(auto_now_add=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'user_cards'
        verbose_name = 'ユーザーカード'
        verbose_name_plural = 'ユーザーカード'
        # unique_together制約を削除して、同じカードを複数枚持てるようにする
        indexes = [
            models.Index(fields=['user', 'obtained_at']),
            models.Index(fields=['old_id']),
            models.Index(fields=['user', 'card']),  # 検索用インデックス
        ]
    
    def __str__(self):
        return f'{self.user.display_id} - {self.card.code}'
