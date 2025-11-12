"""
Lottery Celery tasks.
"""
from celery import shared_task
from django.utils import timezone
from users.models import UserMeta
from lottery.models import JackpotWin
from gamification.models import Title, Card
import logging

logger = logging.getLogger('toybox')


@shared_task
def process_submission_notification(anon_id: str, submission_id: int, title: str = None, card_id: str = None):
    """Process submission notification."""
    try:
        from users.models import User
        user = User.objects.get(display_id=anon_id)  # Adjust based on your user model
        meta = UserMeta.objects.get(user=user)
        notification = {
            'type': 'submission',
            'message': '提出ありがとうございます！',
            'title': title,
            'card_id': card_id,
            'submission_id': submission_id,
            'created_at': timezone.now().isoformat(),
            'read': False,
        }
        notifications = meta.notifications or []
        notifications.insert(0, notification)
        meta.notifications = notifications
        meta.save()
        logger.info('notification.created', extra={'anon_id': anon_id})
    except Exception as e:
        logger.warning('notification.failed', extra={'anon_id': anon_id, 'error': str(e)})


@shared_task
def expire_user_titles_daily():
    """Expire user titles daily."""
    now = timezone.now()
    expired_metas = UserMeta.objects.filter(
        expires_at__lt=now,
        active_title__isnull=False
    )
    
    count = 0
    for meta in expired_metas:
        meta.active_title = None
        meta.title_color = None
        meta.expires_at = None
        meta.save()
        count += 1
    
    logger.info('titles.expired', extra={'count': count})
    return count


@shared_task
def clean_expired_pins():
    """Clean expired pinned jackpot wins."""
    now = timezone.now()
    expired_pins = JackpotWin.objects.filter(
        pinned_until__lt=now,
        pinned_until__isnull=False
    )
    
    count = expired_pins.update(pinned_until=None)
    logger.info('pins.cleaned', extra={'count': count})
    return count


@shared_task
def rotate_seasonal_cards():
    """Rotate seasonal cards (enable/disable based on date)."""
    # TODO: Implement seasonal card rotation logic
    # This would check current date and enable/disable seasonal cards
    logger.info('seasonal_cards.rotated')
    return 0


@shared_task
def rotate_seasonal_titles():
    """Rotate seasonal titles (enable/disable based on date)."""
    # TODO: Implement seasonal title rotation logic
    # This would check current date and enable/disable seasonal titles
    logger.info('seasonal_titles.rotated')
    return 0


@shared_task
def daily_submit_cap_enforcer():
    """Enforce daily submission cap."""
    from submissions.models import Submission
    from lottery.models import LotteryRule
    
    rule = LotteryRule.objects.filter(is_active=True).first()
    if not rule:
        logger.warning('daily_cap.no_rule')
        return 0
    
    from datetime import datetime
    today = timezone.now().date()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # Count submissions per user today
    from django.db.models import Count
    user_counts = Submission.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        deleted_at__isnull=True
    ).values('author').annotate(count=Count('id')).filter(count__gt=rule.daily_cap)
    
    # Log users exceeding cap
    for item in user_counts:
        logger.warning('daily_cap.exceeded', extra={
            'user_id': item['author'],
            'count': item['count'],
            'cap': rule.daily_cap
        })
    
    return len(user_counts)
