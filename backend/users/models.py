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
        extra_fields.setdefault('role', User.Role.ADMIN)
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
        USER = 'USER', 'User'
        OFFICE = 'OFFICE', 'Office'
        AYATORI = 'AYATORI', 'Ayatori'
        ADMIN = 'ADMIN', 'Admin'
    
    # Authentication fields
    email = models.EmailField(unique=True, null=True, blank=True, db_index=True)
    password = models.CharField(max_length=128)  # AbstractBaseUser provides this
    
    # Profile fields
    display_id = models.CharField(max_length=100, db_index=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    
    # Moderation fields
    is_suspended = models.BooleanField(default=False)
    banned_at = models.DateTimeField(null=True, blank=True)
    warning_count = models.IntegerField(default=0)
    warning_notes = models.TextField(blank=True, null=True)
    
    # Django admin fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_id']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['display_id']),
            models.Index(fields=['role']),
            models.Index(fields=['is_suspended']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.display_id} ({self.email})'


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
    
    def __str__(self):
        return f'Registration for {self.user.display_id}'


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
    header_url = models.URLField(max_length=500, blank=True)
    lottery_bonus_count = models.IntegerField(default=0)
    
    # Notifications (JSON array of notification objects)
    notifications = models.JSONField(default=list, blank=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_meta'
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'UserMeta for {self.user.display_id}'


class UserCard(models.Model):
    """User's card collection."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey('gamification.Card', on_delete=models.CASCADE, related_name='user_cards')
    obtained_at = models.DateTimeField(auto_now_add=True)
    
    # ETL tracking
    old_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'user_cards'
        unique_together = [['user', 'card']]
        indexes = [
            models.Index(fields=['user', 'obtained_at']),
            models.Index(fields=['old_id']),
        ]
    
    def __str__(self):
        return f'{self.user.display_id} - {self.card.code}'
