"""
Lottery services.
"""
import uuid
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
                                   title: str = None, caption: str = None, hashtags: list = None,
                                   thumbnail=None, spell: str = None, ai_tool: str = None) -> dict:
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
    
    # Process hashtags (大文字小文字を保持)
    processed_hashtags = []
    if hashtags is not None:
        if not isinstance(hashtags, list):
            raise ValueError('ハッシュタグは配列形式で指定してください。')
        # Filter out empty strings and validate
        for tag in hashtags:
            if tag and isinstance(tag, str) and tag.strip():
                processed_hashtags.append(tag.strip())  # 大文字小文字を保持
        if len(processed_hashtags) > 3:
            raise ValueError('ハッシュタグは3つまでです。')

    spell_clean = ''
    if spell is not None and isinstance(spell, str):
        spell_clean = spell.strip()
        if len(spell_clean) > 8000:
            raise ValueError('呪文（プロンプト）は8000文字までです。')

    ai_tool_key = ''
    if ai_tool is not None and ai_tool != '':
        from submissions.constants import normalize_ai_tool
        ai_tool_key = normalize_ai_tool(str(ai_tool))
        if str(ai_tool).strip() and not ai_tool_key:
            raise ValueError('使用した生成AIの値が不正です。')
    
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
    if thumbnail is not None:
        # サムネイルをJPGに変換して最適化
        from toybox.image_optimizer import optimize_image_to_jpg
        from django.core.files.base import ContentFile
        optimized_thumbnail = optimize_image_to_jpg(
            thumbnail,
            max_width=1024,  # サムネイルは1024pxまで
            max_height=1024,
            quality=85
        )
        
        if optimized_thumbnail:
            # 最適化されたサムネイルをContentFileとして設定
            thumbnail_file = ContentFile(optimized_thumbnail.read())
            thumbnail_file.name = f'thumbnail_{user.id}_{uuid.uuid4().hex[:8]}.jpg'
            submission_data['thumbnail'] = thumbnail_file
        else:
            # 最適化に失敗した場合は元のファイルを使用
            submission_data['thumbnail'] = thumbnail
        logger.info('submission.thumbnail_set', extra={'user_id': user.id})
    
    submission_data['hashtags'] = processed_hashtags
    submission_data['spell'] = spell_clean
    submission_data['ai_tool'] = ai_tool_key
    
    try:
        submission = Submission.objects.create(**submission_data)
        logger.info('submission.created', extra={'user_id': user.id, 'submission_id': submission.id})
        
        # 提出物のURLを検証（ログ出力のみ）
        if image_url:
            from submissions.utils import verify_file_exists
            if not verify_file_exists(image_url):
                logger.warning('submission.image_url_not_found', extra={'user_id': user.id, 'submission_id': submission.id, 'image_url': image_url})
        if video_url:
            from submissions.utils import verify_file_exists
            if not verify_file_exists(video_url):
                logger.warning('submission.video_url_not_found', extra={'user_id': user.id, 'submission_id': submission.id, 'video_url': video_url})
        if game_url:
            from submissions.utils import verify_file_exists
            if not verify_file_exists(game_url):
                logger.warning('submission.game_url_not_found', extra={'user_id': user.id, 'submission_id': submission.id, 'game_url': game_url})
    except Exception as e:
        logger.error('submission.create_failed', extra={'user_id': user.id, 'error': str(e)}, exc_info=True)
        raise
    
    # ポイント付与
    earned_points = 0
    try:
        from gamification.services import award_submission_points
        if game_url:
            sub_type = 'game'
        elif video_url:
            sub_type = 'video'
        else:
            sub_type = 'image'
        earned_points = award_submission_points(user, sub_type)
    except Exception as e:
        logger.warning(f'[Point] submission point award failed: {e}')

    # Grant immediate rewards (card only - v2.0ではカードのみ、称号はアチーブメント制)
    reward = grant_immediate_rewards(meta, boost_rarity=bool(game_url))
    
    # アチーブメント称号チェック（投稿後に新たな称号が解放されていないか確認）
    from gamification.services import check_and_grant_achievement_titles
    newly_granted_titles = check_and_grant_achievement_titles(user)
    
    # 新たに取得した称号があればレスポンスに含める
    reward_title = newly_granted_titles[0] if newly_granted_titles else None
    
    return {
        'jpResult': 'none',
        'probability': 0,
        'bonusCount': meta.lottery_bonus_count,
        'rewardTitle': reward_title,
        'rewardTitleImageUrl': None,
        'rewardCardId': reward.get('card_id'),
        'rewardCard': reward.get('card_meta'),
        'jackpotRecordedAt': None,
        'newlyGrantedTitles': newly_granted_titles,
        'earnedPoints': earned_points,
        'submissionId': str(submission.id),
    }

