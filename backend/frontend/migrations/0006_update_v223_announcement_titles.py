# お知らせに称号追加の記載を追記
from django.db import migrations

ANNOUNCEMENT_TITLE = 'TOYBOX! Ver 2.23 アップデートのお知らせ'
APPEND_LINE = '・各リアクションに対応した称号を9種類追加しました。'


def append_titles_line(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    for ann in Announcement.objects.filter(title=ANNOUNCEMENT_TITLE):
        if APPEND_LINE not in ann.content:
            ann.content = ann.content.replace(
                '  ✨ きれい（3 TP）／ 🥹 エモい！（5 TP）／ 🎮 神ゲー（10 TP）\n',
                '  ✨ きれい（3 TP）／ 🥹 エモい！（5 TP）／ 🎮 神ゲー（10 TP）\n'
                + APPEND_LINE + '\n',
            )
            ann.save(update_fields=['content'])


def remove_titles_line(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    for ann in Announcement.objects.filter(title=ANNOUNCEMENT_TITLE):
        if APPEND_LINE in ann.content:
            ann.content = ann.content.replace(APPEND_LINE + '\n', '')
            ann.save(update_fields=['content'])


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0005_fix_v223_announcement_reaction_names'),
    ]

    operations = [
        migrations.RunPython(append_titles_line, remove_titles_line),
    ]
