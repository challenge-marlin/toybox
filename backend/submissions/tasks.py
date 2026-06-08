"""Submissions app Celery tasks."""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def refresh_reaction_rankings_hourly():
    """1時間ごとにデイリー／週間リアクションランキングを走査・キャッシュ更新。"""
    from submissions.ranking_service import refresh_ranking_cache

    result = refresh_ranking_cache()
    logger.info('refresh_reaction_rankings_hourly: %s', result)
    return result
