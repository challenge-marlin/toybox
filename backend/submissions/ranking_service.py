"""リアクションランキングの集計・キャッシュ・期間フォールバック。

ランキングは「期間内に投稿された作品」に付いたリアクションのみを集計し、
ユーザー単位で順位を決める（同一ユーザーの重複表示・バッジ不一致を防ぐ）。
"""
from __future__ import annotations

from datetime import datetime, timedelta

from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone

CACHE_DAILY_KEY = 'reaction_ranking:daily:v2'
CACHE_WEEKLY_KEY = 'reaction_ranking:weekly:v2'
CACHE_TTL_SECONDS = 3700  # 1時間更新 + 余裕

DAILY_LOOKBACK_DAYS = 90
WEEKLY_LOOKBACK_WEEKS = 52


def _day_bounds(day):
    start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(day, datetime.max.time()))
    return start, end


def _week_bounds(monday):
    sunday = monday + timedelta(days=6)
    start = timezone.make_aware(datetime.combine(monday, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(sunday, datetime.max.time()))
    return start, end


def _daily_period_label(days_ago: int) -> str:
    if days_ago == 0:
        return '本日'
    if days_ago == 1:
        return '昨日'
    return f'{days_ago}日前'


def _weekly_period_label(weeks_ago: int) -> str:
    if weeks_ago == 0:
        return '今週'
    if weeks_ago == 1:
        return '先週'
    return f'{weeks_ago}週間前'


def _reaction_score_case():
    from submissions.views import _reaction_score_case

    return _reaction_score_case()


def _author_display_fields(user):
    meta = getattr(user, 'meta', None)
    is_studysphere = bool(user.studysphere_user_id or user.studysphere_login_code)
    anon_id = 'StudySphereUser' if is_studysphere else user.display_id
    display_name = (meta.display_name if meta and meta.display_name else None) or anon_id
    url_id = user.studysphere_login_code if is_studysphere else user.display_id
    return anon_id, display_name, url_id


def _submission_feed_fields(sub, request=None):
    from submissions.serializers import SubmissionSerializer

    sub_data = SubmissionSerializer(sub, context={'request': request}).data
    display_image_url = sub_data.get('display_image_url') or sub_data.get('image_url') or None
    return {
        'id': str(sub.id),
        'imageUrl': display_image_url,
        'imageThumbnailUrl': display_image_url,
        'displayImageUrl': display_image_url,
        'videoUrl': getattr(sub, 'video_url', None),
        'gameUrl': getattr(sub, 'game_url', None),
        'title': getattr(sub, 'title', None) or None,
        'createdAt': sub.created_at.isoformat() if sub.created_at else None,
        'allReactions': sub_data.get('all_reactions') or [],
    }


def _period_reaction_filter(start, end, *, restrict_submission_dates=True):
    from submissions.models import Reaction

    qs = Reaction.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
        submission__deleted_at__isnull=True,
    )
    if restrict_submission_dates:
        qs = qs.filter(
            submission__created_at__gte=start,
            submission__created_at__lte=end,
        )
    return qs


def _top_submission_for_user_in_period(user_id, start, end, request=None, restrict_submission_dates=True):
    from submissions.models import Submission

    row = (
        _period_reaction_filter(start, end, restrict_submission_dates=restrict_submission_dates)
        .filter(submission__author_id=user_id)
        .values('submission')
        .annotate(sub_score=Sum(_reaction_score_case()))
        .order_by('-sub_score')
        .first()
    )
    if not row or (row['sub_score'] or 0) <= 0:
        return None
    try:
        return Submission.objects.select_related('author', 'author__meta').get(id=row['submission'])
    except Submission.DoesNotExist:
        return None


def _user_ranking_for_period(start, end, limit=10, request=None, restrict_submission_dates=True):
    """期間内投稿に付いたリアクションをユーザー単位で集計したランキング。"""
    from users.models import User

    rows = (
        _period_reaction_filter(start, end, restrict_submission_dates=restrict_submission_dates)
        .values('submission__author')
        .annotate(score=Sum(_reaction_score_case()))
        .order_by('-score')[:limit]
    )

    ranking = []
    user_ranks = {}
    for rank, row in enumerate(rows, start=1):
        score = row['score'] or 0
        if score <= 0:
            continue
        user_id = row['submission__author']
        user_ranks[str(user_id)] = rank
        try:
            user = User.objects.select_related('meta').get(id=user_id)
        except User.DoesNotExist:
            continue

        anon_id, display_name, url_id = _author_display_fields(user)
        entry = {
            'userId': user.id,
            'rank': rank,
            'anonId': anon_id,
            'anonUrlId': url_id,
            'displayName': display_name,
            'score': int(score),
        }
        top_sub = _top_submission_for_user_in_period(
            user_id, start, end, request=request, restrict_submission_dates=restrict_submission_dates
        )
        if top_sub:
            entry.update(_submission_feed_fields(top_sub, request=request))
        ranking.append(entry)

    return ranking, user_ranks


def _all_time_user_ranking(request=None, limit=10):
    from submissions.models import Reaction
    from users.models import User

    rows = (
        Reaction.objects.filter(submission__deleted_at__isnull=True)
        .values('submission__author')
        .annotate(score=Sum(_reaction_score_case()))
        .order_by('-score')[:limit]
    )

    ranking = []
    user_ranks = {}
    for rank, row in enumerate(rows, start=1):
        score = row['score'] or 0
        if score <= 0:
            continue
        user_id = row['submission__author']
        user_ranks[str(user_id)] = rank
        try:
            user = User.objects.select_related('meta').get(id=user_id)
        except User.DoesNotExist:
            continue

        anon_id, display_name, url_id = _author_display_fields(user)
        entry = {
            'userId': user.id,
            'rank': rank,
            'anonId': anon_id,
            'anonUrlId': url_id,
            'displayName': display_name,
            'score': int(score),
        }
        top_row = (
            Reaction.objects.filter(
                submission__author_id=user_id,
                submission__deleted_at__isnull=True,
            )
            .values('submission')
            .annotate(sub_score=Sum(_reaction_score_case()))
            .order_by('-sub_score')
            .first()
        )
        if top_row and (top_row['sub_score'] or 0) > 0:
            from submissions.models import Submission

            try:
                top_sub = Submission.objects.select_related('author', 'author__meta').get(id=top_row['submission'])
                entry.update(_submission_feed_fields(top_sub, request=request))
            except Submission.DoesNotExist:
                pass
        ranking.append(entry)

    return ranking, user_ranks


def _build_period_payload(period, period_start, period_end, is_fallback, period_label, ranking, user_ranks):
    return {
        'ranking': ranking,
        'period': period,
        'periodStart': period_start,
        'periodEnd': period_end,
        'isFallback': is_fallback,
        'periodLabel': period_label,
        'computedAt': timezone.now().isoformat(),
        'userRanks': user_ranks,
    }


def compute_daily_ranking_payload(request=None) -> dict:
    today = timezone.localdate()
    for days_ago in range(DAILY_LOOKBACK_DAYS):
        day = today - timedelta(days=days_ago)
        start, end = _day_bounds(day)
        ranking, user_ranks = _user_ranking_for_period(start, end, request=request)
        if ranking:
            return _build_period_payload(
                'daily', day.isoformat(), day.isoformat(), days_ago > 0,
                _daily_period_label(days_ago), ranking, user_ranks,
            )

    ranking, user_ranks = _all_time_user_ranking(request=request)
    return _build_period_payload('daily', None, None, True, '累計', ranking, user_ranks)


def compute_weekly_ranking_payload(request=None) -> dict:
    today = timezone.localdate()
    this_monday = today - timedelta(days=today.weekday())
    for weeks_ago in range(WEEKLY_LOOKBACK_WEEKS):
        monday = this_monday - timedelta(weeks=weeks_ago)
        start, end = _week_bounds(monday)
        ranking, user_ranks = _user_ranking_for_period(start, end, request=request)
        if ranking:
            return _build_period_payload(
                'weekly', monday.isoformat(), (monday + timedelta(days=6)).isoformat(),
                weeks_ago > 0, _weekly_period_label(weeks_ago), ranking, user_ranks,
            )

    ranking, user_ranks = _all_time_user_ranking(request=request)
    return _build_period_payload('weekly', None, None, True, '累計', ranking, user_ranks)


def refresh_ranking_cache() -> dict:
    """1時間ごとの走査: デイリー／週間ランキングを再集計してキャッシュする。"""
    daily = compute_daily_ranking_payload(request=None)
    weekly = compute_weekly_ranking_payload(request=None)
    cache.set(CACHE_DAILY_KEY, daily, CACHE_TTL_SECONDS)
    cache.set(CACHE_WEEKLY_KEY, weekly, CACHE_TTL_SECONDS)
    return {
        'daily_count': len(daily.get('ranking') or []),
        'weekly_count': len(weekly.get('ranking') or []),
        'daily_label': daily.get('periodLabel'),
        'weekly_label': weekly.get('periodLabel'),
    }


def get_daily_ranking_response(request=None) -> dict:
    cached = cache.get(CACHE_DAILY_KEY)
    if cached:
        return cached
    payload = compute_daily_ranking_payload(request=request)
    cache.set(CACHE_DAILY_KEY, payload, CACHE_TTL_SECONDS)
    return payload


def get_weekly_ranking_response(request=None) -> dict:
    cached = cache.get(CACHE_WEEKLY_KEY)
    if cached:
        return cached
    payload = compute_weekly_ranking_payload(request=request)
    cache.set(CACHE_WEEKLY_KEY, payload, CACHE_TTL_SECONDS)
    return payload


def get_user_badge_ranks(user_id: int) -> dict:
    daily = get_daily_ranking_response(request=None)
    weekly = get_weekly_ranking_response(request=None)
    uid = str(user_id)
    return {
        'daily': daily.get('userRanks', {}).get(uid),
        'weekly': weekly.get('userRanks', {}).get(uid),
    }
