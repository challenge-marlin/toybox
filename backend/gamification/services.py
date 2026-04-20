"""
Gamification services.
"""
from django.utils import timezone
from django.db import transaction
from users.models import UserMeta, User, UserCard
from gamification.models import Card, UserPoint, PointHistory
import random
import logging
import os
import csv

logger = logging.getLogger('toybox')


def load_card_master():
    """Load card master data from TSV file or DB."""
    # Try to load from DB first (if cards are already loaded)
    db_cards = Card.objects.all()
    if db_cards.exists():
        return list(db_cards)
    
    # Fallback: load from TSV file
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tsv_path = os.path.join(project_root, 'src', 'data', 'card_master.small.tsv')
        
        if not os.path.exists(tsv_path):
            logger.warning('Card master TSV file not found, using empty list')
            return []
        
        cards = []
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                card_id = row.get('card_id', '').strip()
                card_name = row.get('card_name', '').strip()
                rarity_str = row.get('rarity', '-').strip()
                image_url = row.get('image_url', '-').strip()
                
                if not card_id or not card_name:
                    continue
                
                # Map TSV rarity to Django rarity
                rarity_map = {
                    'N': 'common',
                    'R': 'rare',
                    'SR': 'seasonal',
                    'SSR': 'special',
                    '-': 'common',
                }
                rarity = rarity_map.get(rarity_str, 'common')
                
                # Handle image_url
                if image_url == '-' or not image_url:
                    image_url = f'/uploads/cards/{card_id}.png'
                
                # 追加項目（TSVにあれば読む、なければコードから推定または空）
                attribute = (row.get('attribute') or '').strip() or None
                atk_raw = (row.get('atk_points') or '').strip()
                atk_points = int(atk_raw) if atk_raw and atk_raw.isdigit() else None
                def_raw = (row.get('def_points') or '').strip()
                def_points = int(def_raw) if def_raw and def_raw.isdigit() else None
                card_type_raw = (row.get('card_type') or '').strip().lower()
                if card_type_raw in ('character', 'effect'):
                    card_type = card_type_raw
                else:
                    # コードから推定: C* → character, E* → effect
                    card_type = 'character' if card_id.startswith('C') else 'effect' if card_id.startswith('E') else None
                buff_effect = (row.get('buff_effect') or '').strip() or None
                description = (row.get('description') or row.get('card_description') or '').strip() or None
                
                # Create card object (not saved to DB, just for in-memory use)
                card = Card(
                    code=card_id,
                    name=card_name,
                    rarity=rarity,
                    image_url=image_url if image_url != '-' else None,
                    description=description,
                    attribute=attribute,
                    atk_points=atk_points,
                    def_points=def_points,
                    card_type=card_type,
                    buff_effect=buff_effect,
                )
                cards.append(card)
        
        return cards
    except Exception as e:
        logger.error(f'Failed to load card master: {e}')
        return []


def grant_immediate_rewards(meta: UserMeta, boost_rarity: bool = False) -> dict:
    """Grant immediate rewards (card only).
    
    v2.0変更: 称号はアチーブメント制に移行したため、投稿時のランダム称号付与を廃止。
    カードのみ付与する。称号は check_and_grant_achievement_titles() で付与される。
    """
    now = timezone.now()
    
    # 称号・期限は変更しない（アチーブメントシステムが管理する）
    title_image_url = None
    chosen_title = None
    
    # Draw card from card master
    card_meta = None
    card_id = None
    
    try:
        # Load card master (from DB or TSV)
        master_cards = load_card_master()
        
        if not master_cards:
            logger.warning('No cards in master, using fallback')
            card_id = f'C{random.randint(1, 20):03d}'
            card_meta = {
                'card_id': card_id,
                'card_name': f'Card {card_id}',
                'rarity': 'N',
                'image_url': None
            }
        else:
            # Filter by card type (50% Character, 50% Effect)
            pick_effect = random.random() < 0.5
            
            # Weighted random by rarity (same as Next.js)
            rarity_weights = {
                'SSR': 0.01,
                'SR': 0.04,
                'R': 0.20,
                'N': 0.75
            }
            
            # Map Django rarity to Next.js format
            rarity_map_reverse = {
                'common': 'N',
                'rare': 'R',
                'seasonal': 'SR',
                'special': 'SSR'
            }
            
            if pick_effect:
                # Effect cards: E101-E136 range
                effect_cards = [c for c in master_cards if c.code.startswith('E')]
                if effect_cards:
                    # Group by rarity
                    by_rarity = {}
                    for c in effect_cards:
                        js_rarity = rarity_map_reverse.get(c.rarity, 'N')
                        if js_rarity not in by_rarity:
                            by_rarity[js_rarity] = []
                        by_rarity[js_rarity].append(c)
                    
                    # Weighted pick
                    total_weight = sum(rarity_weights.values())
                    r = random.random() * total_weight
                    acc = 0
                    selected_rarity = 'N'
                    for rarity, weight in rarity_weights.items():
                        acc += weight
                        if r <= acc:
                            selected_rarity = rarity
                            break
                    
                    # Pick from selected rarity pool
                    pool = by_rarity.get(selected_rarity, [])
                    if pool:
                        card_row = random.choice(pool)
                    else:
                        card_row = random.choice(effect_cards)
                else:
                    card_row = random.choice(master_cards)
            else:
                # Character cards: C001-C020
                char_cards = [c for c in master_cards if c.code.startswith('C')]
                if char_cards:
                    # Group by rarity
                    by_rarity = {}
                    for c in char_cards:
                        js_rarity = rarity_map_reverse.get(c.rarity, 'N')
                        if js_rarity not in by_rarity:
                            by_rarity[js_rarity] = []
                        by_rarity[js_rarity].append(c)
                    
                    # Weighted pick
                    total_weight = sum(rarity_weights.values())
                    r = random.random() * total_weight
                    acc = 0
                    selected_rarity = 'N'
                    for rarity, weight in rarity_weights.items():
                        acc += weight
                        if r <= acc:
                            selected_rarity = rarity
                            break
                    
                    # Pick from selected rarity pool
                    pool = by_rarity.get(selected_rarity, [])
                    if pool:
                        card_row = random.choice(pool)
                    else:
                        card_row = random.choice(char_cards)
                else:
                    card_row = random.choice(master_cards)
            
            card_id = card_row.code
            
            # Get or create Card in DB (for UserCard relationship)
            defaults = {
                'name': card_row.name,
                'rarity': card_row.rarity,
                'image_url': card_row.image_url,
            }
            if hasattr(card_row, 'description') and card_row.description is not None:
                defaults['description'] = card_row.description
            if hasattr(card_row, 'attribute') and card_row.attribute is not None:
                defaults['attribute'] = card_row.attribute
            if hasattr(card_row, 'atk_points') and card_row.atk_points is not None:
                defaults['atk_points'] = card_row.atk_points
            if hasattr(card_row, 'def_points') and card_row.def_points is not None:
                defaults['def_points'] = card_row.def_points
            if hasattr(card_row, 'card_type') and card_row.card_type:
                defaults['card_type'] = card_row.card_type
            if hasattr(card_row, 'buff_effect') and card_row.buff_effect is not None:
                defaults['buff_effect'] = card_row.buff_effect
            db_card, _ = Card.objects.get_or_create(code=card_id, defaults=defaults)
            
            # Create UserCard (allow duplicates - same card can be owned multiple times)
            UserCard.objects.create(
                user=meta.user,
                card=db_card,
                obtained_at=now
            )
            
            # Map Django rarity to Next.js format
            rarity_map_reverse = {
                'common': 'N',
                'rare': 'R',
                'seasonal': 'SR',
                'special': 'SSR'
            }
            rarity = rarity_map_reverse.get(card_row.rarity, 'N')
            
            # Use /uploads/cards/ URL for card images (consistent with frontend)
            image_url = card_row.image_url
            if not image_url or image_url == '-':
                # Use /uploads/cards/ path for card images (works with media.py URL patterns)
                image_url = f'/uploads/cards/{card_id}.png'
            elif image_url.startswith('/static/frontend/uploads/'):
                # Convert /static/frontend/uploads/ to /uploads/ for consistency
                image_url = image_url.replace('/static/frontend/uploads/', '/uploads/')
            
            card_meta = {
                'card_id': card_id,
                'card_name': card_row.name,
                'rarity': rarity,
                'image_url': image_url
            }
    except Exception as e:
        logger.error('reward.card_draw_failed', extra={'error': str(e)}, exc_info=True)
        # Fallback
        card_id = f'C{random.randint(1, 20):03d}'
        card_meta = {
            'card_id': card_id,
            'card_name': f'Card {card_id}',
            'rarity': 'N',
            'image_url': None
        }
    
    meta.save()
    
    logger.info('reward.granted', extra={
        'user_id': meta.user_id,
        'card_id': card_id
    })
    
    return {
        'title': chosen_title,
        'title_image_url': title_image_url,
        'card_id': card_id,
        'card_meta': card_meta
    }


# ============================================================
# 全アチーブメント定義（50種類）
# color: 'green'=入門, 'blue'=初級, 'gold'=中級, 'red'=上級, 'rainbow'=伝説
# secret: True=条件非公開, ultra_secret: True=名前も非公開（？？？表示）
# ============================================================
ACHIEVEMENT_DEFINITIONS = [
    # === 入門 (GREEN) ===
    {'name': '駆け出しクリエイター',    'color': 'green',   'condition_text': 'TOYBOXに登録する',                      'secret': False, 'ultra_secret': False},
    {'name': 'はじめの一歩',            'color': 'green',   'condition_text': '作品を1本投稿する',                     'secret': False, 'ultra_secret': False},
    {'name': '絵師見習い',              'color': 'green',   'condition_text': '画像を1枚投稿する',                     'secret': False, 'ultra_secret': False},
    {'name': '映像クリエイター見習い',  'color': 'green',   'condition_text': '動画を1本投稿する',                     'secret': False, 'ultra_secret': False},
    {'name': 'ゲームメーカー見習い',    'color': 'green',   'condition_text': 'ゲームを1本投稿する',                   'secret': False, 'ultra_secret': False},
    {'name': '注目の新星',              'color': 'green',   'condition_text': 'いいねを10件もらう',                    'secret': False, 'ultra_secret': False},
    {'name': '話題の的',                'color': 'green',   'condition_text': 'リアクションを合計30件もらう',          'secret': False, 'ultra_secret': False},
    {'name': '笑わせ屋',                'color': 'green',   'condition_text': '😂笑えるリアクションを5件もらう',       'secret': False, 'ultra_secret': False},
    {'name': '感動屋',                  'color': 'green',   'condition_text': '😭感動したリアクションを5件もらう',     'secret': False, 'ultra_secret': False},
    {'name': 'かわいいの使い手',        'color': 'green',   'condition_text': '🥰かわいいリアクションを5件もらう',     'secret': False, 'ultra_secret': False},
    {'name': '朝活クリエイター',        'color': 'green',   'condition_text': '朝（6〜9時）に投稿する',               'secret': False, 'ultra_secret': False},
    {'name': '週末クリエイター',        'color': 'green',   'condition_text': '土曜または日曜に投稿する',             'secret': False, 'ultra_secret': False},
    # === 初級 (BLUE) ===
    {'name': '見習いクリエイター',      'color': 'blue',    'condition_text': '作品を5本投稿する',                     'secret': False, 'ultra_secret': False},
    {'name': 'イラストレーター',        'color': 'blue',    'condition_text': '画像を10枚投稿する',                    'secret': False, 'ultra_secret': False},
    {'name': 'ビデオアーティスト',      'color': 'blue',    'condition_text': '動画を5本投稿する',                     'secret': False, 'ultra_secret': False},
    {'name': 'ゲームクリエイター',      'color': 'blue',    'condition_text': 'ゲームを5本投稿する',                   'secret': False, 'ultra_secret': False},
    {'name': '人気クリエイター',        'color': 'blue',    'condition_text': 'いいねを50件もらう',                    'secret': False, 'ultra_secret': False},
    {'name': 'コミュニティの星',        'color': 'blue',    'condition_text': 'リアクションを合計100件もらう',         'secret': False, 'ultra_secret': False},
    {'name': 'クールマン',              'color': 'blue',    'condition_text': '😎かっこいいリアクションを10件もらう',  'secret': False, 'ultra_secret': False},
    {'name': '驚異のクリエイター',      'color': 'blue',    'condition_text': '🤩すごいリアクションを10件もらう',      'secret': False, 'ultra_secret': False},
    {'name': '万能クリエイター',        'color': 'blue',    'condition_text': '画像・動画・ゲームをすべて投稿する',    'secret': False, 'ultra_secret': False},
    {'name': '夜型クリエイター',        'color': 'blue',    'condition_text': '深夜（0〜4時）に投稿する',             'secret': False, 'ultra_secret': False},
    {'name': 'カードコレクター',        'color': 'blue',    'condition_text': 'カードを5枚以上集める',                 'secret': False, 'ultra_secret': False},
    {'name': '3日坊主じゃない',         'color': 'blue',    'condition_text': '3日連続で投稿する',                     'secret': False, 'ultra_secret': False},
    # === 中級 (GOLD) ===
    {'name': '中堅クリエイター',        'color': 'gold',    'condition_text': '作品を20本投稿する',                    'secret': False, 'ultra_secret': False},
    {'name': 'ベテランクリエイター',    'color': 'gold',    'condition_text': '作品を50本投稿する',                    'secret': False, 'ultra_secret': False},
    {'name': 'デジタルアーティスト',    'color': 'gold',    'condition_text': '画像を30枚投稿する',                    'secret': False, 'ultra_secret': False},
    {'name': '動画職人',                'color': 'gold',    'condition_text': '動画を15本投稿する',                    'secret': False, 'ultra_secret': False},
    {'name': 'ゲーム職人',              'color': 'gold',    'condition_text': 'ゲームを10本投稿する',                  'secret': False, 'ultra_secret': False},
    {'name': 'トップクリエイター',      'color': 'gold',    'condition_text': 'いいねを200件もらう',                   'secret': False, 'ultra_secret': False},
    {'name': '感動の嵐',                'color': 'gold',    'condition_text': 'リアクションを合計500件もらう',         'secret': False, 'ultra_secret': False},
    {'name': 'トリプルマスター',        'color': 'gold',    'condition_text': '3ジャンルそれぞれ5本以上投稿する',     'secret': False, 'ultra_secret': False},
    {'name': '一週間の炎',              'color': 'gold',    'condition_text': '7日連続で投稿する',                     'secret': False, 'ultra_secret': False},
    {'name': 'レアコレクター',          'color': 'gold',    'condition_text': 'カードを10枚以上集める',                'secret': False, 'ultra_secret': False},
    # === 上級 (RED, 条件秘密) ===
    {'name': 'マスタークリエイター',    'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': '絵の達人',                'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': '動画の達人',              'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': 'ゲームの達人',            'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': '伝説のスター',            'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': '継続の意志',              'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': '熱狂のクリエイター',      'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    # === 伝説 (RAINBOW) ===
    {'name': 'レジェンドクリエイター',  'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': 'ゲームの神様',            'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    {'name': '創造神',                  'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': False},
    # === 超秘密（名前も非公開） ===
    {'name': '影の芸術家',              'color': 'red',     'condition_text': '？？？',                                'secret': True,  'ultra_secret': True},
    {'name': '深淵のクリエイター',      'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': True},
    {'name': '時を超える者',            'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': True},
    {'name': '全知全能',                'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': True},
    {'name': 'TOYBOXの使者',           'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': True},
    {'name': 'AYATORI',                'color': 'rainbow', 'condition_text': '？？？',                                'secret': True,  'ultra_secret': True},
    # === 特別称号（公式スタッフ専用・他のユーザーには非公開） ===
    {'name': 'TOYBOX!公式',            'color': 'official','condition_text': 'TOYBOX公式スタッフに付与',               'secret': False, 'ultra_secret': False},
]

# 称号名 → カラー の高速参照用
ACHIEVEMENT_COLOR_MAP = {a['name']: a['color'] for a in ACHIEVEMENT_DEFINITIONS}


def _compute_user_stats(user: User) -> dict:
    """全アチーブメント判定に必要な統計を一括計算して返す。"""
    from submissions.models import Submission, Reaction
    from django.db.models import Q
    from zoneinfo import ZoneInfo
    from datetime import timedelta

    JST = ZoneInfo('Asia/Tokyo')

    qs = Submission.objects.filter(author=user, deleted_at__isnull=True)

    total_posts = qs.count()
    game_posts  = qs.exclude(game_url='').exclude(game_url__isnull=True).count()
    video_posts = qs.exclude(video_url='').exclude(video_url__isnull=True)\
                    .filter(Q(game_url__isnull=True) | Q(game_url='')).count()
    image_posts = qs.filter(
        Q(game_url__isnull=True) | Q(game_url=''),
        Q(video_url__isnull=True) | Q(video_url='')
    ).count()

    my_ids = list(qs.values_list('id', flat=True))

    def rxcount(rtype):
        return Reaction.objects.filter(submission_id__in=my_ids, type=rtype).count()

    submit_medal_count = rxcount(Reaction.Type.SUBMIT_MEDAL)
    funny_count        = rxcount(Reaction.Type.FUNNY)
    moved_count        = rxcount(Reaction.Type.MOVED)
    cute_count         = rxcount(Reaction.Type.CUTE)
    cool_count         = rxcount(Reaction.Type.COOL)
    awesome_count      = rxcount(Reaction.Type.AWESOME)
    total_reactions    = Reaction.objects.filter(submission_id__in=my_ids).count()

    card_count = UserCard.objects.filter(user=user).count()

    # 時間帯・曜日・連続日数
    datetimes = list(qs.values_list('created_at', flat=True))
    jst_hours    = [dt.astimezone(JST).hour    for dt in datetimes]
    jst_weekdays = [dt.astimezone(JST).weekday() for dt in datetimes]  # 5=土, 6=日

    has_morning_post = any(6 <= h <= 8 for h in jst_hours)
    has_night_post   = any(0 <= h <= 3 for h in jst_hours)
    has_weekend_post = any(wd >= 5 for wd in jst_weekdays)

    jst_dates = sorted(set(dt.astimezone(JST).date() for dt in datetimes))
    max_streak = current_streak = 0
    prev_date = None
    for d in jst_dates:
        if prev_date is not None and d == prev_date + timedelta(days=1):
            current_streak += 1
        else:
            current_streak = 1
        max_streak = max(max_streak, current_streak)
        prev_date = d

    return {
        'total_posts':       total_posts,
        'game_posts':        game_posts,
        'video_posts':       video_posts,
        'image_posts':       image_posts,
        'submit_medal_count':submit_medal_count,
        'funny_count':       funny_count,
        'moved_count':       moved_count,
        'cute_count':        cute_count,
        'cool_count':        cool_count,
        'awesome_count':     awesome_count,
        'total_reactions':   total_reactions,
        'card_count':        card_count,
        'has_morning_post':  has_morning_post,
        'has_night_post':    has_night_post,
        'has_weekend_post':  has_weekend_post,
        'max_streak':        max_streak,
    }


def _check_achievement(name: str, s: dict) -> bool:
    """統計データ s に基づき、指定した称号の条件を満たしているか返す。"""
    tp  = s['total_posts']
    gp  = s['game_posts']
    ip  = s['image_posts']
    vp  = s['video_posts']
    lk  = s['submit_medal_count']
    tr  = s['total_reactions']
    fn  = s['funny_count']
    mv  = s['moved_count']
    ct  = s['cute_count']
    cl  = s['cool_count']
    aw  = s['awesome_count']
    cc  = s['card_count']
    str_= s['max_streak']

    checks = {
        # 入門 (GREEN)
        '駆け出しクリエイター':   True,
        'はじめの一歩':           tp >= 1,
        '絵師見習い':             ip >= 1,
        '映像クリエイター見習い': vp >= 1,
        'ゲームメーカー見習い':   gp >= 1,
        '注目の新星':             lk >= 10,
        '話題の的':               tr >= 30,
        '笑わせ屋':               fn >= 5,
        '感動屋':                 mv >= 5,
        'かわいいの使い手':       ct >= 5,
        '朝活クリエイター':       s['has_morning_post'],
        '週末クリエイター':       s['has_weekend_post'],
        # 初級 (BLUE)
        '見習いクリエイター':     tp >= 5,
        'イラストレーター':       ip >= 10,
        'ビデオアーティスト':     vp >= 5,
        'ゲームクリエイター':     gp >= 5,
        '人気クリエイター':       lk >= 50,
        'コミュニティの星':       tr >= 100,
        'クールマン':             cl >= 10,
        '驚異のクリエイター':     aw >= 10,
        '万能クリエイター':       ip >= 1 and vp >= 1 and gp >= 1,
        '夜型クリエイター':       s['has_night_post'],
        'カードコレクター':       cc >= 5,
        '3日坊主じゃない':        str_ >= 3,
        # 中級 (GOLD)
        '中堅クリエイター':       tp >= 20,
        'ベテランクリエイター':   tp >= 50,
        'デジタルアーティスト':   ip >= 30,
        '動画職人':               vp >= 15,
        'ゲーム職人':             gp >= 10,
        'トップクリエイター':     lk >= 200,
        '感動の嵐':               tr >= 500,
        'トリプルマスター':       ip >= 5 and vp >= 5 and gp >= 5,
        '一週間の炎':             str_ >= 7,
        'レアコレクター':         cc >= 10,
        # 上級 (RED, 条件秘密)
        'マスタークリエイター':   tp >= 100,
        '絵の達人':               ip >= 100,
        '動画の達人':             vp >= 50,
        'ゲームの達人':           gp >= 20,
        '伝説のスター':           lk >= 500,
        '継続の意志':             str_ >= 30,
        '熱狂のクリエイター':     tr >= 1000,
        # 伝説 (RAINBOW)
        'レジェンドクリエイター': tp >= 300,
        'ゲームの神様':           gp >= 50,
        '創造神':                 ip >= 50 and vp >= 30 and gp >= 20,
        # 超秘密
        '影の芸術家':             vp >= 50,
        '深淵のクリエイター':     lk >= 1000,
        '時を超える者':           str_ >= 60,
        '全知全能':               tp >= 500,
        'TOYBOXの使者':          tr >= 2000,
        'AYATORI':               False,  # 管理者のみ手動付与
    }
    return checks.get(name, False)


def check_and_grant_achievement_titles(user: User) -> list:
    """アチーブメント条件をチェックし、未取得の称号を付与する。
    
    投稿・リアクション受け取りなどのタイミングで呼び出す。
    新たに付与された称号のリストを返す。
    """
    meta, _ = UserMeta.objects.get_or_create(user=user)

    earned = set(meta.earned_titles or [])
    newly_granted = []

    stats = _compute_user_stats(user)

    for defn in ACHIEVEMENT_DEFINITIONS:
        title_name = defn['name']
        if title_name not in earned and _check_achievement(title_name, stats):
            earned.add(title_name)
            newly_granted.append(title_name)
            if not meta.active_title:
                meta.active_title = title_name
                meta.expires_at = None

    if newly_granted:
        meta.earned_titles = list(earned)
        meta.save(update_fields=['earned_titles', 'active_title', 'expires_at'])
        logger.info('achievement.titles_granted', extra={
            'user_id': user.id,
            'newly_granted': newly_granted
        })

    return newly_granted


# ---------------------------------------------------------------------------
# ポイントシステム
# ---------------------------------------------------------------------------

# リアクション種別ごとのポイント
REACTION_POINTS = {
    'submit_medal': 3,   # いいね
    'awesome':      5,   # おどろき
    'cute':         4,   # かわいい
    'funny':        4,   # おもしろい
    'moved':        4,   # 感動した（旧 熱い！相当）
    'cool':         5,   # かっこいい（旧 拍手相当）
}

# 投稿種別ごとのポイント（1件目 / 2件目以降）
SUBMISSION_POINTS = {
    'image': (10, 5),
    'video': (25, 12),
    'game':  (100, 50),
}


def _get_or_create_user_point(user):
    """UserPoint を get_or_create して返す（ロック付き）。"""
    point, _ = UserPoint.objects.get_or_create(user=user)
    return point


@transaction.atomic
def award_points(user, action_type: str, points: int, description: str = '') -> PointHistory:
    """ポイントを付与して履歴を記録する。points は正の整数を想定。"""
    if points <= 0:
        return None

    up = UserPoint.objects.select_for_update().get_or_create(user=user)[0]
    up.total_points += points
    up.save(update_fields=['total_points', 'updated_at'])

    history = PointHistory.objects.create(
        user=user,
        action_type=action_type,
        points=points,
        description=description,
    )
    logger.info(f'[Point] user={user.id} +{points}pt ({action_type}) total={up.total_points}')
    return history


@transaction.atomic
def spend_points(user, action_type: str, points: int, description: str = ''):
    """TP を消費する。残高不足のときは None を返す。"""
    if points <= 0:
        return None
    up = UserPoint.objects.select_for_update().get_or_create(user=user)[0]
    if up.total_points < points:
        return None
    up.total_points -= points
    up.save(update_fields=['total_points', 'updated_at'])
    history = PointHistory.objects.create(
        user=user,
        action_type=action_type,
        points=-points,
        description=(description or '')[:200],
    )
    logger.info(f'[Point] user={user.id} -{points}pt ({action_type}) total={up.total_points}')
    return history


def award_registration_bonus(user) -> bool:
    """初回登録ボーナス（100pt）。既に付与済みなら False を返す。"""
    up, created = UserPoint.objects.get_or_create(user=user)
    if not created:
        # 既にレコードあり → 登録ボーナスが済んでいるか否かは履歴で判断
        if PointHistory.objects.filter(user=user, action_type=PointHistory.ActionType.REGISTRATION_BONUS).exists():
            return False

    award_points(user, PointHistory.ActionType.REGISTRATION_BONUS, 100, '初回登録ボーナス')
    return True


def award_migration_bonus(user) -> bool:
    """既存ユーザー移行ボーナス（100pt）。一人1回限り。"""
    up, _ = UserPoint.objects.get_or_create(user=user)
    if up.migration_bonus_granted:
        return False
    award_points(user, PointHistory.ActionType.MIGRATION_BONUS, 100, '移行ボーナス')
    up.migration_bonus_granted = True
    up.save(update_fields=['migration_bonus_granted', 'updated_at'])
    return True


def award_daily_login(user) -> bool:
    """毎日ログインボーナス（30pt）。1日1回限り。"""
    today = timezone.now().date()
    already = PointHistory.objects.filter(
        user=user,
        action_type=PointHistory.ActionType.DAILY_LOGIN,
        created_at__date=today,
    ).exists()
    if already:
        return False
    award_points(user, PointHistory.ActionType.DAILY_LOGIN, 30, '毎日ログインボーナス')
    return True


def award_submission_points(user, submission_type: str) -> int:
    """
    投稿ポイントを付与する。
    submission_type: 'image' | 'video' | 'game'
    戻り値: 付与したポイント数（0 = 対象外）
    """
    base, half = SUBMISSION_POINTS.get(submission_type, (0, 0))
    if base == 0:
        return 0

    action_map = {
        'image': PointHistory.ActionType.SUBMISSION_IMAGE,
        'video': PointHistory.ActionType.SUBMISSION_VIDEO,
        'game':  PointHistory.ActionType.SUBMISSION_GAME,
    }
    action_type = action_map[submission_type]

    # 当日の同種投稿数を確認
    today = timezone.now().date()
    count_today = PointHistory.objects.filter(
        user=user,
        action_type=action_type,
        created_at__date=today,
    ).count()

    points = base if count_today == 0 else half
    label = {'image': '画像投稿', 'video': '動画投稿', 'game': 'ゲーム投稿'}[submission_type]
    award_points(user, action_type, points, label)
    return points


def award_reaction_received_points(post_author, reaction_type: str) -> int:
    """
    リアクションを受け取ったときに投稿者へポイントを付与する。
    戻り値: 付与したポイント数（0 = 対象外）
    """
    points = REACTION_POINTS.get(reaction_type, 0)
    if points == 0:
        return 0

    emoji_labels = {
        'submit_medal': 'いいね',
        'awesome':      'おどろき',
        'cute':         'かわいい',
        'funny':        'おもしろい',
        'moved':        '感動した',
        'cool':         'かっこいい',
    }
    label = emoji_labels.get(reaction_type, reaction_type)
    award_points(
        post_author,
        PointHistory.ActionType.REACTION_RECEIVED,
        points,
        f'リアクション受取（{label}）',
    )
    return points


def get_point_summary(user) -> dict:
    """ポイント残高と最近の履歴を返す。"""
    up = _get_or_create_user_point(user)
    history = list(
        PointHistory.objects.filter(user=user)
        .order_by('-created_at')[:50]
        .values('action_type', 'points', 'description', 'created_at')
    )
    return {
        'total_points': up.total_points,
        'history': history,
    }


def award_game_played(player, submission) -> dict:
    """
    ゲームが30秒プレイされたときのポイント付与。
    - プレイヤー: 5TP（自分の投稿は対象外、1ゲームにつき1日1回）
    - 投稿者: 10TP（同条件）
    戻り値: {'player_awarded': bool, 'author_awarded': bool}
    """
    if submission.author == player:
        return {'player_awarded': False, 'author_awarded': False}

    today = timezone.now().date()
    sub_id = str(submission.id)

    player_already = PointHistory.objects.filter(
        user=player,
        action_type='game_played_player',
        created_at__date=today,
        description__icontains=sub_id,
    ).exists()
    player_awarded = False
    if not player_already:
        award_points(player, 'game_played_player', 5, f'ゲームをプレイした (id:{sub_id})')
        player_awarded = True

    author_already = PointHistory.objects.filter(
        user=submission.author,
        action_type='game_played_author',
        created_at__date=today,
        description__icontains=f'player:{player.id}',
    ).exists()
    author_awarded = False
    if not author_already:
        award_points(
            submission.author,
            'game_played_author',
            10,
            f'ゲームがプレイされた (id:{sub_id}, player:{player.id})',
        )
        author_awarded = True

    return {'player_awarded': player_awarded, 'author_awarded': author_awarded}
