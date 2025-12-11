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
                
                # Create card object (not saved to DB, just for in-memory use)
                card = Card(
                    code=card_id,
                    name=card_name,
                    rarity=rarity,
                    image_url=image_url if image_url != '-' else None,
                )
                cards.append(card)
        
        return cards
    except Exception as e:
        logger.error(f'Failed to load card master: {e}')
        return []


def grant_immediate_rewards(meta: UserMeta, boost_rarity: bool = False) -> dict:
    """Grant immediate rewards (title + card)."""
    from gamification.models import Title
    
    titles = [
        '蒸気の旅人',
        '真鍮の探究者',
        '歯車の達人',
        '工房の匠',
        '鉄と蒸気の詩人',
        '火花をまとう見習い',
        '真夜中の機巧設計士',
        '歯車仕掛けの物語紡ぎ',
        '蒸気都市の工房守'
    ]
    
    chosen_title = random.choice(titles)
    now = timezone.now()
    until = now + timezone.timedelta(days=7)
    
    meta.active_title = chosen_title
    meta.expires_at = until
    
    # 称号のバナー画像URLを取得
    title_image_url = None
    try:
        title_obj = Title.objects.filter(name=chosen_title).first()
        if title_obj:
            if title_obj.image:
                title_image_url = title_obj.image.url
            elif title_obj.image_url:
                title_image_url = title_obj.image_url
    except Exception as e:
        logger.warning(f'Failed to get title image for {chosen_title}: {e}')
    
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
            db_card, _ = Card.objects.get_or_create(
                code=card_id,
                defaults={
                    'name': card_row.name,
                    'rarity': card_row.rarity,
                    'image_url': card_row.image_url
                }
            )
            
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
        'title': chosen_title,
        'card_id': card_id
    })
    
    return {
        'title': chosen_title,
        'title_image_url': title_image_url,
        'card_id': card_id,
        'card_meta': card_meta
    }

