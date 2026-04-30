"""
Management command to load card master data from TSV file.
"""
import os
import csv
from django.core.management.base import BaseCommand
from gamification.models import Card


class Command(BaseCommand):
    help = 'Load card master data from TSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tsv-file',
            type=str,
            default='src/data/card_master.small.tsv',
            help='Path to TSV file (relative to project root)'
        )

    def handle(self, *args, **options):
        tsv_file = options['tsv_file']
        
        # Resolve path: absolute → そのまま / 相対 → プロジェクトルート基準
        if os.path.isabs(tsv_file):
            tsv_path = tsv_file
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            tsv_path = os.path.join(project_root, tsv_file)
        
        self.stdout.write(f'Reading TSV from: {tsv_path}')
        if not os.path.exists(tsv_path):
            self.stdout.write(self.style.ERROR(f'TSV file not found: {tsv_path}'))
            self.stdout.write('Upload card_master.tsv to server (e.g. /var/www/toybox/backend/src/data/) and pass --tsv-file src/data/card_master.tsv, or use absolute path like /app/src/data/card_master.tsv.')
            return
        
        # Rarity mapping: TSV (N/R/SR/SSR) -> Django (common/rare/seasonal/special)
        rarity_map = {
            'N': 'common',
            'R': 'rare',
            'SR': 'seasonal',
            'SSR': 'special',
            '-': 'common',  # Default for Effect cards
        }
        
        # 日本語列名 → 英語列名のマッピング
        col_aliases = {
            'ID': 'card_id',
            'カード名': 'card_name',
            '種類': 'card_type',
            '属性': 'attribute',
            'ATC': 'atk_points',
            'DEF': 'def_points',
            'レアリティ': 'rarity',
            'デバフ効果（エフェクトのみ）': 'buff_effect',
            'カード説明文（１００文字）': 'description',
        }
        # 種類（日本語）→ card_type（英語）
        card_type_jp = {
            'キャラクター': 'character',
            'エフェクト': 'effect',
        }

        def normalize_row(row):
            """列名を英語に統一し、マスターデータにない列はスキップする"""
            normalized = {}
            for key, value in row.items():
                normalized_key = col_aliases.get(key, key)
                # マスターデータに存在する列名のみ保持
                master_cols = {'card_id', 'card_name', 'rarity', 'image_url', 'attribute',
                               'atk_points', 'def_points', 'card_type', 'buff_effect', 'description'}
                if normalized_key in master_cols:
                    normalized[normalized_key] = value
            return normalized

        loaded_count = 0
        updated_count = 0
        
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            for raw_row in reader:
                row = normalize_row(raw_row)
                card_id = (row.get('card_id') or '').strip()
                card_name = (row.get('card_name') or '').strip()
                rarity_str = (row.get('rarity') or '-').strip()
                image_url_raw = row.get('image_url') or '-'
                image_url = image_url_raw.strip() if image_url_raw else '-'
                attribute = (row.get('attribute') or '').strip() or None
                atk_raw = (row.get('atk_points') or '').strip()
                atk_points = int(atk_raw) if atk_raw and atk_raw.isdigit() else None
                def_raw = (row.get('def_points') or '').strip()
                def_points = int(def_raw) if def_raw and def_raw.isdigit() else None
                card_type_raw = (row.get('card_type') or '').strip()
                # 日本語の種類名を英語に変換
                card_type_raw = card_type_jp.get(card_type_raw, card_type_raw).lower()
                if card_type_raw in ('character', 'effect'):
                    card_type = card_type_raw
                else:
                    card_type = 'character' if card_id.startswith('C') else 'effect' if card_id.startswith('E') else None
                buff_effect = (row.get('buff_effect') or '').strip() or None
                description = (row.get('description') or row.get('card_description') or '').strip() or None
                
                if not card_id or not card_name:
                    continue
                
                # Map rarity
                rarity = rarity_map.get(rarity_str, 'common')
                
                # Handle image_url: if '-', use default path
                if image_url == '-' or not image_url:
                    image_url = f'/uploads/cards/{card_id}.png'
                
                # Debug: print values for C004
                if card_id == 'C004':
                    self.stdout.write(f'[DEBUG C004] TSV values: attr={repr(attribute)}, atk={atk_points}, def={def_points}, desc={repr(description[:30])}')
                
                # Get existing card or create new one
                try:
                    card = Card.objects.get(code=card_id)
                    created = False
                except Card.DoesNotExist:
                    card = Card(code=card_id)
                    created = True
                
                # Set all fields explicitly
                card.name = card_name
                card.rarity = rarity
                card.image_url = image_url if image_url != '-' else None
                card.description = description
                card.attribute = attribute
                card.atk_points = atk_points
                card.def_points = def_points
                card.card_type = card_type
                card.buff_effect = buff_effect
                card.save()
                
                # Debug: verify saved values for C004
                if card_id == 'C004':
                    card.refresh_from_db()
                    self.stdout.write(f'[DEBUG C004] After save: attr={repr(card.attribute)}, atk={card.atk_points}, def={card.def_points}, desc={repr((card.description or "")[:30])}')
                
                if created:
                    loaded_count += 1
                    try:
                        self.stdout.write(self.style.SUCCESS(f'Created: {card.code} - {card.name} ({rarity})'))
                    except UnicodeEncodeError:
                        self.stdout.write(self.style.SUCCESS(f'Created: {card.code} ({rarity})'))
                else:
                    updated_count += 1
                    try:
                        self.stdout.write(f'Updated: {card.code} - {card.name} ({rarity})')
                    except UnicodeEncodeError:
                        self.stdout.write(f'Updated: {card.code} ({rarity})')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nLoaded {loaded_count} new cards, updated {updated_count} existing cards.'
        ))
        self.stdout.write(f'Total cards in database: {Card.objects.count()}')

