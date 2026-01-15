#!/usr/bin/env python
"""称号の画像設定を確認するスクリプト"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toybox.settings.dev')
django.setup()

from gamification.models import Title
from pathlib import Path
from django.conf import settings

print("=" * 60)
print("称号の画像設定を確認")
print("=" * 60)

titles = Title.objects.all().order_by('name')
for title in titles:
    print(f"\n称号名: {title.name}")
    print(f"  ImageField: {title.image}")
    print(f"  image_url: {title.image_url}")
    
    # 画像ファイルの存在確認
    if title.image_url:
        if title.image_url.startswith('/uploads/titles/'):
            image_name = title.image_url.replace('/uploads/titles/', '')
            image_path = Path(settings.MEDIA_ROOT) / 'titles' / image_name
            exists = image_path.exists()
            print(f"  画像ファイル: {image_path}")
            print(f"  存在: {exists}")
        else:
            print(f"  画像URL: {title.image_url} (外部URLまたは別形式)")
    elif title.image:
        # ImageFieldが設定されている場合
        image_path = Path(settings.MEDIA_ROOT) / title.image.name
        exists = image_path.exists()
        print(f"  ImageFieldパス: {image_path}")
        print(f"  存在: {exists}")

print("\n" + "=" * 60)
print("確認完了")
print("=" * 60)
