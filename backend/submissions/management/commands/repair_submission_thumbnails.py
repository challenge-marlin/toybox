"""
投稿のサムネイル画像のデータベースを修復するコマンド
/uploads/submissions/thumbnails/ に存在するファイルから、データベースのthumbnailフィールドを修復します
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pathlib import Path
from django.conf import settings
from submissions.models import Submission
import os
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Repair submission thumbnail images in database from existing files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode (no database updates)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_root = Path(settings.MEDIA_ROOT)
        thumbnails_dir = media_root / 'submissions' / 'thumbnails'
        
        if not thumbnails_dir.exists():
            self.stdout.write(self.style.ERROR(f'Thumbnails directory not found: {thumbnails_dir}'))
            return
        
        self.stdout.write(f'Scanning thumbnails directory: {thumbnails_dir}')
        
        # ファイルをリストアップ
        files = list(thumbnails_dir.glob('*'))
        self.stdout.write(f'Found {len(files)} thumbnail files')
        
        repaired_count = 0
        matched_count = 0
        
        # まず、game_urlが存在するがthumbnailが空のSubmissionをリストアップ
        submissions_without_thumbnail = Submission.objects.filter(
            game_url__isnull=False
        ).exclude(game_url='').filter(
            thumbnail__isnull=True
        ) | Submission.objects.filter(
            game_url__isnull=False
        ).exclude(game_url='').filter(
            thumbnail=''
        )
        
        self.stdout.write(f'Found {submissions_without_thumbnail.count()} submissions with game_url but no thumbnail')
        
        # ファイル名からSubmission IDを推測するパターン
        # DjangoのImageFieldは通常、{field_name}_{id}_{uuid}.{ext}の形式を使用
        # または、{id}_{timestamp}.{ext}の形式もあり得る
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            filename = file_path.name
            self.stdout.write(f'Processing: {filename}')
            
            # ファイル名からSubmission IDを抽出を試みる
            # パターン1: thumbnail_{id}_{uuid}.{ext}
            # パターン2: {id}_{timestamp}.{ext}
            # パターン3: {id}_{uuid}.{ext}
            
            submission_id = None
            
            # パターン1を試す
            match = re.match(r'thumbnail_(\d+)_', filename)
            if match:
                submission_id = int(match.group(1))
            else:
                # パターン2を試す（数字で始まる）
                match = re.match(r'^(\d+)_', filename)
                if match:
                    submission_id = int(match.group(1))
            
            if submission_id:
                try:
                    submission = Submission.objects.get(id=submission_id)
                    if submission.game_url and not submission.thumbnail:
                        # ファイルパスを構築
                        relative_path = f'submissions/thumbnails/{filename}'
                        if not dry_run:
                            # ImageFieldにファイルパスを設定
                            # 注意: ImageFieldはファイルオブジェクトを必要とするため、
                            # 既存のファイルを開いて設定する必要がある
                            with open(file_path, 'rb') as f:
                                from django.core.files import File
                                submission.thumbnail.save(filename, File(f), save=True)
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  → Submission {submission_id}: thumbnail set from {filename}'
                                )
                            )
                            repaired_count += 1
                        else:
                            self.stdout.write(
                                f'  → Submission {submission_id}: would set thumbnail from {filename}'
                            )
                            matched_count += 1
                    else:
                        if submission.thumbnail:
                            self.stdout.write(f'  → Submission {submission_id}: already has thumbnail')
                        else:
                            self.stdout.write(f'  → Submission {submission_id}: no game_url')
                except Submission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  → Submission {submission_id} not found'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  → Error processing {filename}: {e}'))
            else:
                # ファイル名からIDを抽出できない場合、作成日時から推測を試みる
                # ファイルの更新日時を取得
                file_mtime = os.path.getmtime(file_path)
                from datetime import datetime
                from django.utils import timezone
                file_time = timezone.make_aware(datetime.fromtimestamp(file_mtime))
                
                # 作成日時が近いSubmissionを探す（±1時間以内）
                from datetime import timedelta
                time_range_start = file_time - timedelta(hours=1)
                time_range_end = file_time + timedelta(hours=1)
                
                candidates = submissions_without_thumbnail.filter(
                    created_at__gte=time_range_start,
                    created_at__lte=time_range_end
                )
                
                if candidates.count() == 1:
                    submission = candidates.first()
                    if not dry_run:
                        with open(file_path, 'rb') as f:
                            from django.core.files import File
                            submission.thumbnail.save(filename, File(f), save=True)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  → Submission {submission.id} (matched by time): thumbnail set from {filename}'
                            )
                        )
                        repaired_count += 1
                    else:
                        self.stdout.write(
                            f'  → Submission {submission.id} (matched by time): would set thumbnail from {filename}'
                        )
                        matched_count += 1
                elif candidates.count() > 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  → Multiple candidates found for {filename} (time-based matching)'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  → Could not match {filename} to any submission'
                        )
                    )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\nDry run mode: Would repair {matched_count} records'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nRepaired {repaired_count} records'))
