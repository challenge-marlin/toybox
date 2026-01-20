"""
既存の画像をJPGに変換して最適化するコマンド
元のファイルは保持し、最適化されたJPGを生成します
"""
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from toybox.image_optimizer import convert_and_save_image
import os

class Command(BaseCommand):
    help = 'Optimize existing images to JPG format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (no file conversions)',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['profiles', 'submissions', 'thumbnails', 'all'],
            default='all',
            help='Type of images to optimize',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        image_type = options['type']
        media_root = Path(settings.MEDIA_ROOT)
        
        optimized_count = 0
        error_count = 0
        
        # プロフィール画像
        if image_type in ('profiles', 'all'):
            self.stdout.write('=== Processing profile images ===')
            profiles_dir = media_root / 'profiles'
            if profiles_dir.exists():
                for file_path in profiles_dir.glob('*'):
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() in ('.jpg', '.jpeg'):
                        continue  # 既にJPGの場合はスキップ
                    
                    self.stdout.write(f'Processing: {file_path.name}')
                    if not dry_run:
                        # 最適化されたファイル名を生成
                        optimized_filename = f"{file_path.stem}_opt.jpg"
                        optimized_path = f'profiles/{optimized_filename}'
                        
                        success, saved_path = convert_and_save_image(
                            str(file_path),
                            optimized_path,
                            max_width=1920 if 'header' in file_path.stem else 512,
                            max_height=1920 if 'header' in file_path.stem else 512,
                            quality=85,
                            preserve_original=True
                        )
                        
                        if success:
                            self.stdout.write(self.style.SUCCESS(f'  → Optimized: {saved_path}'))
                            optimized_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'  → Failed to optimize'))
                            error_count += 1
                    else:
                        self.stdout.write(f'  → Would optimize: {file_path.name}')
                        optimized_count += 1
        
        # 投稿画像
        if image_type in ('submissions', 'all'):
            self.stdout.write('\n=== Processing submission images ===')
            submissions_dir = media_root / 'submissions'
            if submissions_dir.exists():
                for file_path in submissions_dir.glob('*'):
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() in ('.jpg', '.jpeg'):
                        continue  # 既にJPGの場合はスキップ
                    if file_path.name.startswith('thumbnail'):
                        continue  # サムネイルは別で処理
                    
                    self.stdout.write(f'Processing: {file_path.name}')
                    if not dry_run:
                        optimized_filename = f"{file_path.stem}_opt.jpg"
                        optimized_path = f'submissions/{optimized_filename}'
                        
                        success, saved_path = convert_and_save_image(
                            str(file_path),
                            optimized_path,
                            max_width=1920,
                            max_height=1920,
                            quality=85,
                            preserve_original=True
                        )
                        
                        if success:
                            self.stdout.write(self.style.SUCCESS(f'  → Optimized: {saved_path}'))
                            optimized_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'  → Failed to optimize'))
                            error_count += 1
                    else:
                        self.stdout.write(f'  → Would optimize: {file_path.name}')
                        optimized_count += 1
        
        # サムネイル画像
        if image_type in ('thumbnails', 'all'):
            self.stdout.write('\n=== Processing thumbnail images ===')
            thumbnails_dir = media_root / 'submissions' / 'thumbnails'
            if thumbnails_dir.exists():
                for file_path in thumbnails_dir.glob('*'):
                    if not file_path.is_file():
                        continue
                    if file_path.suffix.lower() in ('.jpg', '.jpeg'):
                        continue  # 既にJPGの場合はスキップ
                    
                    self.stdout.write(f'Processing: {file_path.name}')
                    if not dry_run:
                        optimized_filename = f"{file_path.stem}_opt.jpg"
                        optimized_path = f'submissions/thumbnails/{optimized_filename}'
                        
                        success, saved_path = convert_and_save_image(
                            str(file_path),
                            optimized_path,
                            max_width=1024,
                            max_height=1024,
                            quality=85,
                            preserve_original=True
                        )
                        
                        if success:
                            self.stdout.write(self.style.SUCCESS(f'  → Optimized: {saved_path}'))
                            optimized_count += 1
                        else:
                            self.stdout.write(self.style.ERROR(f'  → Failed to optimize'))
                            error_count += 1
                    else:
                        self.stdout.write(f'  → Would optimize: {file_path.name}')
                        optimized_count += 1
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDry run mode: Would optimize {optimized_count} images'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nOptimized {optimized_count} images'))
            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'Failed to optimize {error_count} images'))
