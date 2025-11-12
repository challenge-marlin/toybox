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
        
        # Resolve path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        tsv_path = os.path.join(project_root, tsv_file)
        
        if not os.path.exists(tsv_path):
            self.stdout.write(self.style.ERROR(f'TSV file not found: {tsv_path}'))
            return
        
        # Rarity mapping: TSV (N/R/SR/SSR) -> Django (common/rare/seasonal/special)
        rarity_map = {
            'N': 'common',
            'R': 'rare',
            'SR': 'seasonal',
            'SSR': 'special',
            '-': 'common',  # Default for Effect cards
        }
        
        loaded_count = 0
        updated_count = 0
        
        with open(tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            for row in reader:
                card_id = row.get('card_id', '').strip()
                card_name = row.get('card_name', '').strip()
                rarity_str = row.get('rarity', '-').strip()
                image_url = row.get('image_url', '-').strip()
                
                if not card_id or not card_name:
                    continue
                
                # Map rarity
                rarity = rarity_map.get(rarity_str, 'common')
                
                # Handle image_url: if '-', use default path
                if image_url == '-' or not image_url:
                    image_url = f'/uploads/cards/{card_id}.png'
                
                # Create or update card
                card, created = Card.objects.update_or_create(
                    code=card_id,
                    defaults={
                        'name': card_name,
                        'rarity': rarity,
                        'image_url': image_url if image_url != '-' else None,
                    }
                )
                
                if created:
                    loaded_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created: {card.code} - {card.name} ({rarity})'))
                else:
                    updated_count += 1
                    self.stdout.write(f'Updated: {card.code} - {card.name} ({rarity})')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nLoaded {loaded_count} new cards, updated {updated_count} existing cards.'
        ))
        self.stdout.write(f'Total cards in database: {Card.objects.count()}')

