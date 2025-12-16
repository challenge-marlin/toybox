"""
Django management command for loading legacy MongoDB data.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import sys
import os

# mongo_to_pgモジュールが存在する場合のみインポート（オプショナル）
MongoToPGMigrator = None

# Add scripts directory to path
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts')
if os.path.exists(scripts_dir):
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    # mongo_to_pgモジュールが存在する場合のみインポート
    try:
        from mongo_to_pg import MongoToPGMigrator
    except ImportError:
        # mongo_to_pgモジュールが存在しない場合はNoneとして扱う
        MongoToPGMigrator = None


class Command(BaseCommand):
    help = 'Load legacy data from MongoDB to PostgreSQL'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mongo-uri',
            type=str,
            default='mongodb://localhost:27017/',
            help='MongoDB connection URI'
        )
        parser.add_argument(
            '--mongo-db',
            type=str,
            default='toybox',
            help='MongoDB database name'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (no actual data migration)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of records per collection'
        )
        parser.add_argument(
            '--offset',
            type=int,
            default=0,
            help='Offset for records'
        )
        parser.add_argument(
            '--collection',
            choices=['users', 'user_meta', 'submissions', 'reactions', 'cards', 'jackpot_wins', 'discord_shares', 'all'],
            default='all',
            help='Collection to migrate'
        )
    
    def handle(self, *args, **options):
        if MongoToPGMigrator is None:
            self.stdout.write(self.style.ERROR('mongo_to_pg module not found. Please install it or ensure scripts/mongo_to_pg.py exists.'))
            return
        
        mongo_uri = options['mongo_uri']
        mongo_db = options['mongo_db']
        dry_run = options['dry_run']
        limit = options.get('limit')
        offset = options.get('offset', 0)
        collection = options.get('collection', 'all')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))
        
        migrator = MongoToPGMigrator(mongo_uri, mongo_db, dry_run)
        
        if collection == 'all' or collection == 'users':
            self.stdout.write('Migrating users...')
            migrator.migrate_users(limit, offset)
        
        if collection == 'all' or collection == 'user_meta':
            self.stdout.write('Migrating userMeta...')
            migrator.migrate_user_meta(limit, offset)
        
        if collection == 'all' or collection == 'submissions':
            self.stdout.write('Migrating submissions...')
            migrator.migrate_submissions(limit, offset)
        
        if collection == 'all' or collection == 'reactions':
            self.stdout.write('Migrating reactions...')
            migrator.migrate_reactions(limit, offset)
        
        if collection == 'all' or collection == 'cards':
            self.stdout.write('Migrating cards...')
            migrator.migrate_cards(limit, offset)
        
        if collection == 'all' or collection == 'jackpot_wins':
            self.stdout.write('Migrating jackpotWins...')
            migrator.migrate_jackpot_wins(limit, offset)
        
        if collection == 'all' or collection == 'discord_shares':
            self.stdout.write('Migrating discordShares...')
            migrator.migrate_discord_shares(limit, offset)
        
        migrator.print_stats()
        
        self.stdout.write(self.style.SUCCESS('Migration completed!'))

