"""
Adminpanel app signals for audit logging.
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AdminAuditLog

User = get_user_model()


@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    """Track user changes for audit log."""
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            instance._previous_is_suspended = old_instance.is_suspended
            instance._previous_banned_at = old_instance.banned_at
            instance._previous_warning_count = old_instance.warning_count
        except User.DoesNotExist:
            instance._previous_is_suspended = None
            instance._previous_banned_at = None
            instance._previous_warning_count = None
    else:
        instance._previous_is_suspended = None
        instance._previous_banned_at = None
        instance._previous_warning_count = None


@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user creation and updates."""
    # Skip logging for normal user updates unless it's a moderation action
    if created:
        # Only log if created by admin (will be set by view)
        # For normal user registration, skip audit log
        return
    
    # Check for moderation changes
    if not hasattr(instance, '_previous_is_suspended'):
        # No previous state tracked, skip
        return
    
    changes = {}
    action = None
    
    if instance._previous_is_suspended != instance.is_suspended:
        action = AdminAuditLog.Action.SUSPEND if instance.is_suspended else AdminAuditLog.Action.UNSUSPEND
        changes['is_suspended'] = instance.is_suspended
    elif instance._previous_banned_at != instance.banned_at:
        action = AdminAuditLog.Action.BAN if instance.banned_at else AdminAuditLog.Action.UNBAN
        changes['banned_at'] = str(instance.banned_at) if instance.banned_at else None
    elif instance._previous_warning_count != instance.warning_count:
        action = AdminAuditLog.Action.WARN
        changes['warning_count'] = instance.warning_count
    
    # Only log if there's a moderation action
    if action:
        AdminAuditLog.objects.create(
            actor=None,  # Will be set by view if admin action
            target_user=instance,
            action=action,
            payload=changes
        )


@receiver(post_save, sender='submissions.Submission')
def log_submission_changes(sender, instance, created, **kwargs):
    """Log submission creation and updates."""
    # Skip logging for normal submission creation
    if created:
        return
    
    # Check for soft delete
    if instance.deleted_at:
        AdminAuditLog.objects.create(
            actor=None,
            target_user=instance.author,
            target_submission=instance,
            action=AdminAuditLog.Action.DELETE,
            payload={'delete_reason': instance.delete_reason}
        )
    elif instance.deleted_at is None and hasattr(instance, '_previous_deleted_at') and instance._previous_deleted_at:
        AdminAuditLog.objects.create(
            actor=None,
            target_user=instance.author,
            target_submission=instance,
            action=AdminAuditLog.Action.RESTORE,
            payload={'action': 'restored'}
        )


@receiver(pre_save, sender='submissions.Submission')
def track_submission_changes(sender, instance, **kwargs):
    """Track submission changes for audit log."""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._previous_deleted_at = old_instance.deleted_at
        except sender.DoesNotExist:
            instance._previous_deleted_at = None


@receiver(post_save, sender='sharing.DiscordShare')
def log_discord_share(sender, instance, created, **kwargs):
    """Log Discord share actions."""
    # Skip logging for normal Discord shares (only log admin actions)
    pass
