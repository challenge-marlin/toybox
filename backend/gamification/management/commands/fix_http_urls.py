"""
データベースに保存されているHTTPのURLをHTTPSに変換するコマンド
"""
from django.core.management.base import BaseCommand
from gamification.models import Title


class Command(BaseCommand):
    help = 'データベースに保存されているHTTPのURLをHTTPSに変換します'

    def handle(self, *args, **options):
        """HTTPのURLをHTTPSに変換"""
        titles = Title.objects.filter(image_url__startswith='http://toybox.ayatori-inc.co.jp')
        updated_count = 0
        
        for title in titles:
            old_url = title.image_url
            title.image_url = title.image_url.replace('http://', 'https://', 1)
            title.save(update_fields=['image_url'])
            updated_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f'称号 "{title.name}" のURLを更新: {old_url} -> {title.image_url}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n完了: {updated_count}件の称号URLをHTTPSに変換しました')
        )
