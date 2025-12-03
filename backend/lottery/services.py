"""
Lottery services.
"""
from django.utils import timezone
from django.db import models
from datetime import datetime
from submissions.models import Submission
from users.models import UserMeta, User
from gamification.services import grant_immediate_rewards
import logging

logger = logging.getLogger('toybox')


def has_submitted_today(user: User) -> bool:
    """Check if user has submitted today."""
    today = timezone.now().date()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    return Submission.objects.filter(
        author=user,
        created_at__gte=start,
        created_at__lte=end,
        deleted_at__isnull=True
    ).exists()


def handle_submission_and_lottery(user: User, aim: str, steps: list, frame_type: str,
                                   image_url: str = None, video_url: str = None, game_url: str = None,
                                   title: str = None, caption: str = None, hashtags: list = None) -> dict:
    """Handle submission and lottery processing."""
    # Check for duplicate submissions (within 10 seconds)
    ten_seconds_ago = timezone.now() - timezone.timedelta(seconds=10)
    duplicate = Submission.objects.filter(
        author=user,
        created_at__gte=ten_seconds_ago,
        deleted_at__isnull=True
    )
    if image_url or game_url:
        duplicate = duplicate.filter(
            models.Q(image_url=image_url) if image_url else models.Q(game_url=game_url)
        )
    else:
        duplicate = duplicate.filter(aim=aim, steps=steps, frame_type=frame_type)
    
    if duplicate.exists():
        logger.info('submit.duplicate_skipped', extra={'user_id': user.id})
        meta, _ = UserMeta.objects.get_or_create(user=user)
        return {
            'jpResult': 'none',
            'probability': 0,
            'bonusCount': meta.lottery_bonus_count,
            'rewardTitle': None,
            'rewardCardId': None,
            'rewardCard': None,
            'jackpotRecordedAt': None,
        }
    
    # Get or create UserMeta
    meta, _ = UserMeta.objects.get_or_create(user=user)
    
    # Validate new fields
    if title is not None:
        title = title.strip() if isinstance(title, str) else ''
        if len(title) > 20:
            raise ValueError('題名は20文字までです。')
    
    if caption is not None:
        caption = caption.strip() if isinstance(caption, str) else ''
        if len(caption) > 140:
            raise ValueError('キャプションは140文字までです。')
    
    # Process hashtags
    processed_hashtags = []
    if hashtags is not None:
        if not isinstance(hashtags, list):
            raise ValueError('ハッシュタグは配列形式で指定してください。')
        # Filter out empty strings and validate
        for tag in hashtags:
            if tag and isinstance(tag, str) and tag.strip():
                processed_hashtags.append(tag.strip())
        if len(processed_hashtags) > 3:
            raise ValueError('ハッシュタグは3つまでです。')
    
    # Create submission
    submission_data = {
        'author': user,
        'aim': aim,
        'steps': steps,
        'frame_type': frame_type,
        'image_url': image_url,
        'video_url': video_url,
        'game_url': game_url,
        'jp_result': 'none',
    }
    # Add new fields if provided
    if title is not None:
        submission_data['title'] = title
    if caption is not None:
        submission_data['caption'] = caption
    submission_data['hashtags'] = processed_hashtags
    
    try:
        submission = Submission.objects.create(**submission_data)
        logger.info('submission.created', extra={'user_id': user.id, 'submission_id': submission.id})
    except Exception as e:
        logger.error('submission.create_failed', extra={'user_id': user.id, 'error': str(e)}, exc_info=True)
        raise
    
    # Grant immediate rewards (title + card)
    reward = grant_immediate_rewards(meta, boost_rarity=bool(game_url))
    
    return {
        'jpResult': 'none',
        'probability': 0,
        'bonusCount': meta.lottery_bonus_count,
        'rewardTitle': reward.get('title'),
        'rewardCardId': reward.get('card_id'),
        'rewardCard': reward.get('card_meta'),
        'jackpotRecordedAt': None,
    }

