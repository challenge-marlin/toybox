"""
称号データを初期化し、画像ファイルを関連付ける管理コマンド。

画像の参照順:
1. MEDIA_ROOT/titles/{称号名}.png があればそれを使用
2. なければ frontend/static/frontend/hero/toybox-title.png を
   MEDIA_ROOT/titles/{称号名}.png にコピーしてから DB の image_url を設定
"""
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from gamification.models import Title


# デフォルト画像（static に存在するもの）
DEFAULT_TITLE_IMAGE = Path(__file__).resolve().parent.parent.parent.parent / 'frontend' / 'static' / 'frontend' / 'hero' / 'toybox-title.png'


class Command(BaseCommand):
    help = '称号データを初期化し、画像ファイルを関連付けます'

    def handle(self, *args, **options):
        titles_data = [
            '蒸気の旅人',
            '真鍮の探究者',
            '歯車の達人',
            '工房の匠',
            '鉄と蒸気の詩人',
            '火花をまとう見習い',
            '真夜中の機巧設計士',
            '歯車仕掛けの物語紡ぎ',
            '蒸気都市の工房守'
        ]
        
        titles_dir = Path(settings.MEDIA_ROOT) / 'titles'
        titles_dir.mkdir(parents=True, exist_ok=True)
        created_count = 0
        updated_count = 0
        
        for title_name in titles_data:
            image_path = titles_dir / f'{title_name}.png'
            image_url = None
            
            if image_path.exists():
                image_url = f'/uploads/titles/{title_name}.png'
                self.stdout.write(f'画像ファイルが見つかりました: {image_path.name}')
            else:
                # デフォルト画像をコピーして DB に紐付ける
                if DEFAULT_TITLE_IMAGE.exists():
                    try:
                        shutil.copy2(DEFAULT_TITLE_IMAGE, image_path)
                        image_url = f'/uploads/titles/{title_name}.png'
                        self.stdout.write(self.style.SUCCESS(
                            f'デフォルト画像をコピーしました: {image_path.name}'
                        ))
                    except OSError as e:
                        self.stdout.write(self.style.WARNING(
                            f'画像のコピーに失敗しました: {image_path.name} ({e})'
                        ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'画像が見つかりません: {image_path.name} （デフォルト: {DEFAULT_TITLE_IMAGE} もなし）'
                    ))
            
            title, created = Title.objects.get_or_create(
                name=title_name,
                defaults={
                    'duration_days': 7,
                    'image_url': image_url
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'称号を作成しました: {title_name}'))
            else:
                if image_url and title.image_url != image_url:
                    title.image_url = image_url
                    title.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'称号を更新しました: {title_name} (画像URLを設定)'
                    ))
                elif title.image_url:
                    self.stdout.write(f'称号は既に存在します: {title_name} (画像URL: {title.image_url})')
                else:
                    self.stdout.write(f'称号は既に存在します: {title_name} (画像URL未設定)')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n完了: {created_count}件作成、{updated_count}件更新'
        ))
        self.stdout.write(f'総称号数: {Title.objects.count()}')




