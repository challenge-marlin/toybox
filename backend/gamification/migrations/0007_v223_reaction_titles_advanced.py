# Ver 2.23: 新リアクション称号（上級・伝説・超越）
from django.db import migrations

NEW_TITLES = [
    ('美の化身', '#ef4444'),
    ('エモの神託', '#ef4444'),
    ('神ゲーの覇者', '#ef4444'),
    ('きらめきの伝説', '#a855f7'),
    ('エモの伝説', '#a855f7'),
    ('神ゲーの神話', '#a855f7'),
    ('きらめきの極星', '#00e5ff'),
    ('エモの星雲', '#00e5ff'),
    ('神ゲーの宇宙', '#00e5ff'),
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
        ('gamification', '0006_v223_reaction_titles'),
    ]

    operations = [
        migrations.RunPython(register_titles, unregister_titles),
    ]
