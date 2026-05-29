# お知らせ内のリアクション名を修正（うっとり／ぐっときた → きれい／エモい！）
from django.db import migrations

ANNOUNCEMENT_TITLE = 'TOYBOX! Ver 2.23 アップデートのお知らせ'

OLD_LINE = '  ✨ うっとり（3 TP）／ 🥹 ぐっときた（5 TP）／ 🎮 神ゲー（10 TP）'
NEW_LINE = '  ✨ きれい（3 TP）／ 🥹 エモい！（5 TP）／ 🎮 神ゲー（10 TP）'


def fix_reaction_names(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    for ann in Announcement.objects.filter(title=ANNOUNCEMENT_TITLE):
        if OLD_LINE in ann.content:
            ann.content = ann.content.replace(OLD_LINE, NEW_LINE)
            ann.save(update_fields=['content'])


def revert_reaction_names(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    for ann in Announcement.objects.filter(title=ANNOUNCEMENT_TITLE):
        if NEW_LINE in ann.content:
            ann.content = ann.content.replace(NEW_LINE, OLD_LINE)
            ann.save(update_fields=['content'])


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0004_announcement_v223'),
    ]

    operations = [
        migrations.RunPython(fix_reaction_names, revert_reaction_names),
    ]
