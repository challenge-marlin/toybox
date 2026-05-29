# Ver 2.23: 新リアクション（きれい・エモい！・神ゲー）用称号マスター登録
from django.db import migrations

NEW_TITLES = [
    ('きれいの使い手', '#22c55e'),
    ('エモの伝え手', '#22c55e'),
    ('神ゲー見習い', '#22c55e'),
    ('輝きの職人', '#3b82f6'),
    ('心を揺らす者', '#3b82f6'),
    ('神ゲーの証人', '#3b82f6'),
    ('美の達人', '#eab308'),
    ('エモの巨匠', '#eab308'),
    ('神ゲーの王者', '#eab308'),
]


def register_titles(apps, schema_editor):
    Title = apps.get_model('gamification', 'Title')
    for name, color in NEW_TITLES:
        Title.objects.get_or_create(
            name=name,
            defaults={'color': color, 'duration_days': 0},
        )


def unregister_titles(apps, schema_editor):
    Title = apps.get_model('gamification', 'Title')
    Title.objects.filter(name__in=[n for n, _ in NEW_TITLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gamification', '0005_add_userpoint_pointhistory'),
    ]

    operations = [
        migrations.RunPython(register_titles, unregister_titles),
    ]
