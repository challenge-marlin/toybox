"""
管理コマンド: 指定ユーザーに「TOYBOX!公式」称号を付与する。

使用例:
    docker exec backend-web-1 python manage.py grant_official_title
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

OFFICIAL_DISPLAY_IDS = ['ramchan', 'km1010']
OFFICIAL_TITLE = 'TOYBOX!公式'


class Command(BaseCommand):
    help = '公式スタッフユーザーに「TOYBOX!公式」称号を付与します。'

    def handle(self, *args, **options):
        from users.models import UserMeta

        for display_id in OFFICIAL_DISPLAY_IDS:
            try:
                user = User.objects.get(display_id=display_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'ユーザーが見つかりません: {display_id}'))
                continue

            meta, _ = UserMeta.objects.get_or_create(user=user)
            earned = list(meta.earned_titles or [])

            if OFFICIAL_TITLE in earned:
                self.stdout.write(f'スキップ（付与済み）: {display_id}')
                continue

            earned.append(OFFICIAL_TITLE)
            meta.earned_titles = earned
            meta.save(update_fields=['earned_titles'])
            self.stdout.write(self.style.SUCCESS(f'付与完了: {display_id} → {OFFICIAL_TITLE}'))
