#!/usr/bin/env python
"""称号一覧を確認するスクリプト"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'toybox.settings.development')
django.setup()

from gamification.models import Title

titles = Title.objects.all()
print(f'登録されている称号数: {titles.count()}')
print('\n称号一覧:')
if titles.count() > 0:
    for t in titles:
        print(f'  - {t.name} (色: {t.color or "未設定"}, 有効期間: {t.duration_days}日)')
else:
    print('  データベースに称号が登録されていません。')
    print('\nコード内で定義されている称号（ハードコード）:')
    print('  - 蒸気の旅人')
    print('  - 真鍮の探究者')
    print('  - 歯車の達人')
    print('  - 工房の匠')
    print('  - 鉄と蒸気の詩人')
    print('\n※ これらの称号は`gamification/services.py`の`grant_immediate_rewards`関数内でハードコードされています。')



