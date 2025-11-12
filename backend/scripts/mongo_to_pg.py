"""
MongoDB to PostgreSQL migration script.
"""
import os
import sys
import django
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pymongo
from pymongo import MongoClient
from django.utils import timezone
from django.db import transaction

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toybox.settings.dev')
django.setup()

from users.models import User, UserMeta, UserCard, UserRegistration
from submissions.models import Submission, Reaction
from lottery.models import JackpotWin, LotteryRule
from sharing.models import DiscordShare
from gamification.models import Title, Card
from adminpanel.models import AdminAuditLog


class MongoToPGMigrator:
    """MongoDB to PostgreSQL migrator."""
    
    def __init__(self, mongo_uri: str, mongo_db: str, dry_run: bool = False):
        """Initialize migrator."""
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_db]
        self.dry_run = dry_run
        self.stats = {
            'users': 0,
            'user_meta': 0,
            'submissions': 0,
            'reactions': 0,
            'cards': 0,
            'user_cards': 0,
            'jackpot_wins': 0,
            'discord_shares': 0,
            'errors': []
        }
    
    def migrate_users(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate users collection."""
        collection = self.db['users']
        cursor = collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                if self.dry_run:
                    print(f"[DRY RUN] Would migrate user: {doc.get('_id')}")
                    self.stats['users'] += 1
                    continue
                
                # Map MongoDB user to Django User
                user, created = User.objects.get_or_create(
                    old_id=str(doc['_id']),
                    defaults={
                        'email': doc.get('email'),
                        'display_id': doc.get('displayId') or doc.get('anonId') or doc.get('username'),
                        'username': doc.get('username'),
                        'role': self._map_role(doc.get('role', 'USER')),
                        'avatar_url': doc.get('avatarUrl'),
                        'is_suspended': doc.get('isSuspended', False) or doc.get('suspended', False),
                        'banned_at': self._parse_datetime(doc.get('bannedAt')) if doc.get('bannedAt') else None,
                        'warning_count': doc.get('warningCount', 0) or len(doc.get('warnings', [])),
                        'warning_notes': '\n'.join(doc.get('warnings', [])) if doc.get('warnings') else None,
                    }
                )
                
                if not created:
                    # Update existing user
                    user.email = doc.get('email') or user.email
                    user.display_id = doc.get('displayId') or doc.get('anonId') or user.display_id
                    user.role = self._map_role(doc.get('role', 'USER'))
                    user.avatar_url = doc.get('avatarUrl') or user.avatar_url
                    user.is_suspended = doc.get('isSuspended', False) or doc.get('suspended', False)
                    if doc.get('bannedAt'):
                        user.banned_at = self._parse_datetime(doc.get('bannedAt'))
                    user.warning_count = doc.get('warningCount', 0) or len(doc.get('warnings', []))
                    if doc.get('warnings'):
                        user.warning_notes = '\n'.join(doc.get('warnings', []))
                    user.save()
                
                # Set password if available
                if doc.get('password'):
                    user.set_password(doc['password'])
                    user.save()
                
                self.stats['users'] += 1
                
                # Log import
                AdminAuditLog.objects.create(
                    actor=None,
                    target_user=user,
                    action=AdminAuditLog.Action.IMPORT,
                    payload={'action': 'IMPORT', 'old_id': str(doc['_id'])}
                )
                
            except Exception as e:
                error_msg = f"Error migrating user {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def migrate_user_meta(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate userMeta collection."""
        collection = self.db['userMeta']
        cursor = collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                # Find user by old_id or anon_id
                anon_id = doc.get('anonId') or doc.get('_id')
                user = None
                
                # Try to find by old_id first
                if doc.get('_id'):
                    try:
                        user = User.objects.get(old_id=str(doc['_id']))
                    except User.DoesNotExist:
                        pass
                
                # Try to find by anon_id/display_id
                if not user:
                    try:
                        user = User.objects.get(display_id=anon_id)
                    except User.DoesNotExist:
                        print(f"User not found for userMeta {doc.get('_id')}, skipping")
                        continue
                
                if self.dry_run:
                    print(f"[DRY RUN] Would migrate userMeta for user: {user.id}")
                    self.stats['user_meta'] += 1
                    continue
                
                # Calculate expires_at
                expires_at = None
                if doc.get('activeTitleUntil'):
                    expires_at = self._parse_datetime(doc['activeTitleUntil'])
                elif doc.get('activeTitle'):
                    # Default to created_at + 7 days if no expiration
                    created_at = self._parse_datetime(doc.get('createdAt')) or timezone.now()
                    expires_at = created_at + timedelta(days=7)
                
                meta, created = UserMeta.objects.get_or_create(
                    user=user,
                    defaults={
                        'active_title': doc.get('activeTitle'),
                        'title_color': doc.get('titleColor'),
                        'expires_at': expires_at,
                        'bio': doc.get('bio'),
                        'header_url': doc.get('headerUrl'),
                        'lottery_bonus_count': doc.get('lotteryBonusCount', 0),
                        'old_id': str(doc.get('_id', '')),
                    }
                )
                
                if not created:
                    meta.active_title = doc.get('activeTitle') or meta.active_title
                    meta.title_color = doc.get('titleColor') or meta.title_color
                    meta.expires_at = expires_at or meta.expires_at
                    meta.bio = doc.get('bio') or meta.bio
                    meta.header_url = doc.get('headerUrl') or meta.header_url
                    meta.lottery_bonus_count = doc.get('lotteryBonusCount', 0) or meta.lottery_bonus_count
                    meta.save()
                
                self.stats['user_meta'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating userMeta {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def migrate_submissions(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate submissions collection."""
        collection = self.db['submissions']
        cursor = collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                # Find author
                submitter_id = doc.get('submitterAnonId') or doc.get('authorId')
                author = None
                
                if submitter_id:
                    try:
                        author = User.objects.get(display_id=submitter_id)
                    except User.DoesNotExist:
                        print(f"Author not found for submission {doc.get('_id')}, skipping")
                        continue
                
                if not author:
                    print(f"No author found for submission {doc.get('_id')}, skipping")
                    continue
                
                if self.dry_run:
                    print(f"[DRY RUN] Would migrate submission: {doc.get('_id')}")
                    self.stats['submissions'] += 1
                    continue
                
                # Map deleted flag to deleted_at
                deleted_at = None
                if doc.get('deleted') or doc.get('isDeleted'):
                    deleted_at = self._parse_datetime(doc.get('deletedAt')) or timezone.now()
                
                submission, created = Submission.objects.get_or_create(
                    old_id=str(doc['_id']),
                    defaults={
                        'author': author,
                        'image': doc.get('imageUrl') or doc.get('image'),
                        'caption': doc.get('caption') or doc.get('aim', ''),
                        'comment_enabled': doc.get('commentEnabled', True),
                        'status': self._map_submission_status(doc.get('status', 'PUBLIC')),
                        'deleted_at': deleted_at,
                        'delete_reason': doc.get('deleteReason'),
                        'created_at': self._parse_datetime(doc.get('createdAt')) or timezone.now(),
                    }
                )
                
                if not created:
                    submission.image = doc.get('imageUrl') or doc.get('image') or submission.image
                    submission.caption = doc.get('caption') or doc.get('aim', '') or submission.caption
                    submission.comment_enabled = doc.get('commentEnabled', True)
                    submission.status = self._map_submission_status(doc.get('status', 'PUBLIC'))
                    submission.deleted_at = deleted_at or submission.deleted_at
                    submission.delete_reason = doc.get('deleteReason') or submission.delete_reason
                    submission.save()
                
                self.stats['submissions'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating submission {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def migrate_reactions(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate reactions (from submissions or separate collection)."""
        # Reactions might be embedded in submissions or in a separate collection
        collection = self.db.get('reactions') or self.db['submissions']
        
        cursor = collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                # If reactions collection exists, process it directly
                if collection.name == 'reactions':
                    submission_id = doc.get('submissionId')
                    user_id = doc.get('userId') or doc.get('anonId')
                    reaction_type = doc.get('type', 'submit_medal')
                    
                    submission = None
                    user = None
                    
                    if submission_id:
                        try:
                            submission = Submission.objects.get(old_id=str(submission_id))
                        except Submission.DoesNotExist:
                            continue
                    
                    if user_id:
                        try:
                            user = User.objects.get(display_id=user_id)
                        except User.DoesNotExist:
                            continue
                    
                    if not submission or not user:
                        continue
                    
                    if self.dry_run:
                        print(f"[DRY RUN] Would migrate reaction: {doc.get('_id')}")
                        self.stats['reactions'] += 1
                        continue
                    
                    Reaction.objects.get_or_create(
                        user=user,
                        submission=submission,
                        type=Reaction.Type.SUBMIT_MEDAL,
                        defaults={}
                    )
                    self.stats['reactions'] += 1
                
                # If reactions are embedded in submissions, process them
                elif 'likes' in doc or 'reactions' in doc:
                    submission_id = str(doc.get('_id'))
                    try:
                        submission = Submission.objects.get(old_id=submission_id)
                    except Submission.DoesNotExist:
                        continue
                    
                    # Process likes/reactions
                    likes = doc.get('likes', []) or doc.get('reactions', [])
                    for like_doc in likes:
                        user_id = like_doc if isinstance(like_doc, str) else like_doc.get('anonId') or like_doc.get('userId')
                        if not user_id:
                            continue
                        
                        try:
                            user = User.objects.get(display_id=user_id)
                        except User.DoesNotExist:
                            continue
                        
                        if self.dry_run:
                            self.stats['reactions'] += 1
                            continue
                        
                        Reaction.objects.get_or_create(
                            user=user,
                            submission=submission,
                            type=Reaction.Type.SUBMIT_MEDAL,
                            defaults={}
                        )
                        self.stats['reactions'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating reaction {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def migrate_cards(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate cards and user cards."""
        # Migrate card master data
        cards_collection = self.db.get('cards')
        if cards_collection:
            cursor = cards_collection.find().skip(offset)
            if limit:
                cursor = cursor.limit(limit)
            
            for doc in cursor:
                try:
                    if self.dry_run:
                        print(f"[DRY RUN] Would migrate card: {doc.get('code')}")
                        self.stats['cards'] += 1
                        continue
                    
                    Card.objects.get_or_create(
                        old_id=str(doc.get('_id', '')),
                        defaults={
                            'code': doc.get('code') or doc.get('id'),
                            'rarity': self._map_card_rarity(doc.get('rarity', 'common')),
                        }
                    )
                    self.stats['cards'] += 1
                except Exception as e:
                    error_msg = f"Error migrating card {doc.get('_id')}: {str(e)}"
                    print(error_msg)
                    self.stats['errors'].append(error_msg)
        
        # Migrate user cards from userMeta.cardsAlbum
        user_meta_collection = self.db['userMeta']
        cursor = user_meta_collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                anon_id = doc.get('anonId') or doc.get('_id')
                try:
                    user = User.objects.get(display_id=anon_id)
                except User.DoesNotExist:
                    continue
                
                cards_album = doc.get('cardsAlbum', []) or doc.get('cards', [])
                for card_data in cards_album:
                    card_code = card_data if isinstance(card_data, str) else card_data.get('code') or card_data.get('id')
                    if not card_code:
                        continue
                    
                    try:
                        card = Card.objects.get(code=card_code)
                    except Card.DoesNotExist:
                        # Create card if it doesn't exist
                        card, _ = Card.objects.get_or_create(
                            code=card_code,
                            defaults={'rarity': 'common'}
                        )
                    
                    if self.dry_run:
                        self.stats['user_cards'] += 1
                        continue
                    
                    obtained_at = None
                    if isinstance(card_data, dict):
                        obtained_at = self._parse_datetime(card_data.get('obtainedAt'))
                    
                    UserCard.objects.get_or_create(
                        user=user,
                        card=card,
                        defaults={
                            'obtained_at': obtained_at or timezone.now()
                        }
                    )
                    self.stats['user_cards'] += 1
                    
            except Exception as e:
                error_msg = f"Error migrating user cards for {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def migrate_jackpot_wins(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate jackpotWins collection."""
        collection = self.db['jackpotWins']
        cursor = collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                # Find user
                user_id = doc.get('userId') or doc.get('anonId')
                user = None
                
                if user_id:
                    try:
                        user = User.objects.get(display_id=user_id)
                    except User.DoesNotExist:
                        print(f"User not found for jackpotWin {doc.get('_id')}, skipping")
                        continue
                
                if not user:
                    continue
                
                if self.dry_run:
                    print(f"[DRY RUN] Would migrate jackpotWin: {doc.get('_id')}")
                    self.stats['jackpot_wins'] += 1
                    continue
                
                won_at = self._parse_datetime(doc.get('wonAt')) or self._parse_datetime(doc.get('createdAt')) or timezone.now()
                pinned_until = None
                if doc.get('pinnedUntil'):
                    pinned_until = self._parse_datetime(doc['pinnedUntil'])
                elif won_at:
                    # Default to won_at + 24h if not set
                    pinned_until = won_at + timedelta(hours=24)
                
                # Find submission if available
                submission = None
                if doc.get('submissionId'):
                    try:
                        submission = Submission.objects.get(old_id=str(doc['submissionId']))
                    except Submission.DoesNotExist:
                        pass
                
                JackpotWin.objects.get_or_create(
                    old_id=str(doc['_id']),
                    defaults={
                        'user': user,
                        'submission': submission,
                        'won_at': won_at,
                        'pinned_until': pinned_until,
                    }
                )
                self.stats['jackpot_wins'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating jackpotWin {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def migrate_discord_shares(self, limit: Optional[int] = None, offset: int = 0):
        """Migrate discordShares collection."""
        collection = self.db['discordShares']
        cursor = collection.find().skip(offset)
        if limit:
            cursor = cursor.limit(limit)
        
        for doc in cursor:
            try:
                # Find user
                user_id = doc.get('userId') or doc.get('anonId')
                user = None
                
                if user_id:
                    try:
                        user = User.objects.get(display_id=user_id)
                    except User.DoesNotExist:
                        print(f"User not found for discordShare {doc.get('_id')}, skipping")
                        continue
                
                if not user:
                    continue
                
                if self.dry_run:
                    print(f"[DRY RUN] Would migrate discordShare: {doc.get('_id')}")
                    self.stats['discord_shares'] += 1
                    continue
                
                # Find submission if available
                submission = None
                if doc.get('submissionId'):
                    try:
                        submission = Submission.objects.get(old_id=str(doc['submissionId']))
                    except Submission.DoesNotExist:
                        pass
                
                DiscordShare.objects.get_or_create(
                    old_id=str(doc['_id']),
                    defaults={
                        'user': user,
                        'submission': submission,
                        'share_channel': doc.get('channel') or doc.get('shareChannel', 'general'),
                        'message_id': doc.get('messageId'),
                        'shared_at': self._parse_datetime(doc.get('sharedAt')) or self._parse_datetime(doc.get('createdAt')) or timezone.now(),
                    }
                )
                self.stats['discord_shares'] += 1
                
            except Exception as e:
                error_msg = f"Error migrating discordShare {doc.get('_id')}: {str(e)}"
                print(error_msg)
                self.stats['errors'].append(error_msg)
    
    def _map_role(self, role: str) -> str:
        """Map MongoDB role to Django role."""
        role_map = {
            'USER': User.Role.USER,
            'OFFICE': User.Role.OFFICE,
            'AYATORI': User.Role.AYATORI,
            'ADMIN': User.Role.ADMIN,
        }
        return role_map.get(role.upper(), User.Role.USER)
    
    def _map_submission_status(self, status: str) -> str:
        """Map MongoDB submission status to Django status."""
        status_map = {
            'PUBLIC': Submission.Status.PUBLIC,
            'PRIVATE': Submission.Status.PRIVATE,
            'FLAGGED': Submission.Status.FLAGGED,
        }
        return status_map.get(status.upper(), Submission.Status.PUBLIC)
    
    def _map_card_rarity(self, rarity: str) -> str:
        """Map MongoDB card rarity to Django rarity."""
        rarity_map = {
            'common': Card.Rarity.COMMON,
            'rare': Card.Rarity.RARE,
            'seasonal': Card.Rarity.SEASONAL,
            'special': Card.Rarity.SPECIAL,
        }
        return rarity_map.get(rarity.lower(), Card.Rarity.COMMON)
    
    def _parse_datetime(self, dt) -> Optional[datetime]:
        """Parse datetime from MongoDB document."""
        if not dt:
            return None
        
        if isinstance(dt, datetime):
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        
        if isinstance(dt, str):
            try:
                return timezone.make_aware(datetime.fromisoformat(dt.replace('Z', '+00:00')))
            except:
                pass
        
        return None
    
    def print_stats(self):
        """Print migration statistics."""
        print("\n=== Migration Statistics ===")
        for key, value in self.stats.items():
            if key != 'errors':
                print(f"{key}: {value}")
        if self.stats['errors']:
            print(f"\nErrors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate MongoDB to PostgreSQL')
    parser.add_argument('--mongo-uri', default='mongodb://localhost:27017/', help='MongoDB connection URI')
    parser.add_argument('--mongo-db', default='toybox', help='MongoDB database name')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--limit', type=int, help='Limit number of records per collection')
    parser.add_argument('--offset', type=int, default=0, help='Offset for records')
    parser.add_argument('--collection', choices=['users', 'user_meta', 'submissions', 'reactions', 'cards', 'jackpot_wins', 'discord_shares', 'all'], default='all', help='Collection to migrate')
    
    args = parser.parse_args()
    
    migrator = MongoToPGMigrator(args.mongo_uri, args.mongo_db, args.dry_run)
    
    if args.collection == 'all' or args.collection == 'users':
        print("Migrating users...")
        migrator.migrate_users(args.limit, args.offset)
    
    if args.collection == 'all' or args.collection == 'user_meta':
        print("Migrating userMeta...")
        migrator.migrate_user_meta(args.limit, args.offset)
    
    if args.collection == 'all' or args.collection == 'submissions':
        print("Migrating submissions...")
        migrator.migrate_submissions(args.limit, args.offset)
    
    if args.collection == 'all' or args.collection == 'reactions':
        print("Migrating reactions...")
        migrator.migrate_reactions(args.limit, args.offset)
    
    if args.collection == 'all' or args.collection == 'cards':
        print("Migrating cards...")
        migrator.migrate_cards(args.limit, args.offset)
    
    if args.collection == 'all' or args.collection == 'jackpot_wins':
        print("Migrating jackpotWins...")
        migrator.migrate_jackpot_wins(args.limit, args.offset)
    
    if args.collection == 'all' or args.collection == 'discord_shares':
        print("Migrating discordShares...")
        migrator.migrate_discord_shares(args.limit, args.offset)
    
    migrator.print_stats()

