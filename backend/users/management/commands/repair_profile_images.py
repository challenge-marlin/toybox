"""
プロフィール画像のデータベースを修復するコマンド
/uploads/profiles/ に存在するファイルから、データベースのavatar_urlとheader_urlを修復します
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pathlib import Path
from django.conf import settings
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Repair profile image URLs in database from existing files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (no database updates)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = Path(settings.MEDIA_ROOT)
        profiles_dir = media_root / 'profiles'
        
        if not profiles_dir.exists():
            self.stdout.write(self.style.ERROR(f'Profiles directory not found: {profiles_dir}'))
            return
        
        self.stdout.write(f'Scanning profiles directory: {profiles_dir}')
        
        # ファイル名からユーザーIDを抽出
        # 形式: avatar_{user_id}_{uuid}.{ext} または header_{user_id}_{uuid}.{ext}
        files = list(profiles_dir.glob('*'))
        self.stdout.write(f'Found {len(files)} files')
        
        repaired_count = 0
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            filename = file_path.name
            self.stdout.write(f'Processing: {filename}')
            
            # ファイル名からタイプとユーザーIDを抽出
            if filename.startswith('avatar_'):
                parts = filename.split('_')
                if len(parts) >= 2:
                    try:
                        user_id = int(parts[1])
                        relative_url = f'/uploads/profiles/{filename}'
                        absolute_url = f'https://toybox.ayatori-inc.co.jp{relative_url}'
                        
                        try:
                            user = User.objects.get(id=user_id)
                            if not user.avatar_url or user.avatar_url != absolute_url:
                                if not dry_run:
                                    user.avatar_url = absolute_url
                                    user.save(update_fields=['avatar_url'])
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'  → User {user_id} ({user.display_id}): avatar_url = {absolute_url}'
                                    )
                                )
                                repaired_count += 1
                            else:
                                self.stdout.write(f'  → User {user_id}: avatar_url already correct')
                        except User.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'  → User {user_id} not found'))
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f'  → Could not parse user ID from: {filename}'))
            
            elif filename.startswith('header_'):
                parts = filename.split('_')
                if len(parts) >= 2:
                    try:
                        user_id = int(parts[1])
                        relative_url = f'/uploads/profiles/{filename}'
                        absolute_url = f'https://toybox.ayatori-inc.co.jp{relative_url}'
                        
                        try:
                            user = User.objects.get(id=user_id)
                            from users.models import UserMeta
                            meta, _ = UserMeta.objects.get_or_create(user=user)
                            if not meta.header_url or meta.header_url != absolute_url:
                                if not dry_run:
                                    meta.header_url = absolute_url
                                    meta.save(update_fields=['header_url'])
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'  → User {user_id} ({user.display_id}): header_url = {absolute_url}'
                                    )
                                )
                                repaired_count += 1
                            else:
                                self.stdout.write(f'  → User {user_id}: header_url already correct')
                        except User.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'  → User {user_id} not found'))
                    except ValueError:
                        self.stdout.write(self.style.WARNING(f'  → Could not parse user ID from: {filename}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDry run mode: Would repair {repaired_count} records'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nRepaired {repaired_count} records'))
