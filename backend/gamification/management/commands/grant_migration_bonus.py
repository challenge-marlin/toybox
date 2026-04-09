"""
管理コマンド: 既存ユーザー全員にポイント移行ボーナス（100pt）を付与する。
一人に対して1回限りで、migration_bonus_granted フラグで重複防止。

使用例:
    docker exec backend-web-1 python manage.py grant_migration_bonus
    docker exec backend-web-1 python manage.py grant_migration_bonus --dry-run
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = '既存ユーザー全員にポイント移行ボーナス（100pt）を付与します。'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='実際に付与せず対象ユーザー数だけ表示する',
        )

    def handle(self, *args, **options):
        from gamification.services import award_migration_bonus

        dry_run = options['dry_run']
        users = User.objects.filter(is_active=True)
        total = users.count()
        granted = 0
        skipped = 0

        self.stdout.write(f'対象ユーザー数: {total}')
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] 実際には付与しません'))

        for user in users:
            if dry_run:
                from gamification.models import UserPoint
                up, _ = UserPoint.objects.get_or_create(user=user)
                if up.migration_bonus_granted:
                    skipped += 1
                else:
                    granted += 1
            else:
                result = award_migration_bonus(user)
                if result:
                    granted += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'付与: {granted}名 / スキップ（付与済み）: {skipped}名'
        ))
