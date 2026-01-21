"""
既存画像のサムネイルを生成する管理コマンド
"""
from django.core.management.base import BaseCommand
from pathlib import Path
from django.conf import settings
from toybox.image_optimizer import create_thumbnail_from_path
import os


class Command(BaseCommand):
    help = 'Generate thumbnails for existing images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['profiles', 'submissions', 'all'],
            default='all',
            help='Type of images to process (profiles, submissions, or all)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of existing thumbnails'
        )

    def handle(self, *args, **options):
        image_type = options['type']
        force = options['force']
        
        media_root = Path(settings.MEDIA_ROOT)
        
        if image_type in ('profiles', 'all'):
            self.stdout.write('Processing profile images...')
            self.process_directory(media_root / 'profiles', force)
        
        if image_type in ('submissions', 'all'):
            self.stdout.write('Processing submission images...')
            self.process_directory(media_root / 'submissions', force)
        
        self.stdout.write(self.style.SUCCESS('Thumbnail generation completed!'))

    def process_directory(self, directory: Path, force: bool = False):
        """指定されたディレクトリ内の画像ファイルのサムネイルを生成"""
        if not directory.exists():
            self.stdout.write(self.style.WARNING(f'Directory not found: {directory}'))
            return
        
        # 画像ファイルを検索（_thumb.jpgで終わるファイルは除外）
        image_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        image_files = [
            f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
            and not f.name.endswith('_thumb.jpg')
        ]
        
        self.stdout.write(f'Found {len(image_files)} image files in {directory}')
        
        processed = 0
        skipped = 0
        errors = 0
        
        for image_file in image_files:
            # サムネイルファイル名を生成
            thumbnail_filename = f"{image_file.stem}_thumb.jpg"
            thumbnail_path = image_file.parent / thumbnail_filename
            
            # 既にサムネイルが存在する場合はスキップ（forceがTrueの場合は除く）
            if thumbnail_path.exists() and not force:
                skipped += 1
                continue
            
            try:
                # サムネイルを生成
                relative_source = image_file.relative_to(Path(settings.MEDIA_ROOT))
                relative_thumbnail = thumbnail_path.relative_to(Path(settings.MEDIA_ROOT))
                
                success, saved_path = create_thumbnail_from_path(
                    str(image_file),
                    str(relative_thumbnail),
                    max_size=300,
                    quality=80
                )
                
                if success:
                    processed += 1
                    self.stdout.write(f'  ✓ Generated: {relative_thumbnail}')
                else:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed: {image_file.name}'))
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Error processing {image_file.name}: {e}'))
        
        self.stdout.write(f'Processed: {processed}, Skipped: {skipped}, Errors: {errors}')
