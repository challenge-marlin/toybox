"""
Gamification services.
"""
from django.utils import timezone
from users.models import UserMeta, User, UserCard
from gamification.models import Card
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


def check_and_grant_achievement_titles(user: User) -> list:
    """アチーブメント条件をチェックし、未取得の称号を付与する。
    
    投稿・リアクション受け取りなどのタイミングで呼び出す。
    新たに付与された称号のリストを返す。
    """
    from gamification.models import Title
    from submissions.models import Submission
    
    meta, _ = UserMeta.objects.get_or_create(user=user)
    
    # 既取得の称号名セット（UserMeta.earned_titles JSONフィールド）
    earned = set(meta.earned_titles or [])
    newly_granted = []
    
    # 投稿数を取得
    total_posts = Submission.objects.filter(author=user, deleted_at__isnull=True).count()
    game_posts = Submission.objects.filter(author=user, deleted_at__isnull=True).exclude(game_url='').exclude(game_url__isnull=True).count()
    
    # 定義: (称号名, 達成条件チェック関数)
    achievements = [
        ('駆け出しクリエイター', lambda: True),           # 登録直後・常に対象
        ('見習いクリエイター',   lambda: total_posts >= 5),
        ('中堅クリエイター',     lambda: total_posts >= 20),
        ('ベテランクリエイター', lambda: total_posts >= 50),
        ('ゲームメーカー見習い', lambda: game_posts >= 1),
        ('ゲームクリエイター',   lambda: game_posts >= 5),
    ]
    
    for title_name, condition in achievements:
        if title_name not in earned and condition():
            earned.add(title_name)
            newly_granted.append(title_name)
            # 最初の称号をアクティブに設定（アクティブ称号が未設定の場合のみ）
            if not meta.active_title:
                meta.active_title = title_name
                meta.expires_at = None  # 有効期限なし
    
    if newly_granted:
        meta.earned_titles = list(earned)
        meta.save(update_fields=['earned_titles', 'active_title', 'expires_at'])
        logger.info('achievement.titles_granted', extra={
            'user_id': user.id,
            'newly_granted': newly_granted
        })
    
    return newly_granted

