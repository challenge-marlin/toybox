"""
全ユーザーに「駆け出しクリエイター」称号を付与し、既存の有効期限をクリアする。
また、称号マスターに「駆け出しクリエイター」が存在しなければ作成する。
"""
from django.db import migrations


STARTER_TITLE = '駆け出しクリエイター'


def grant_starter_title(apps, schema_editor):
    UserMeta = apps.get_model('users', 'UserMeta')
    Title = apps.get_model('gamification', 'Title')

    # 称号マスターに登録されていなければ作成
    Title.objects.get_or_create(
        name=STARTER_TITLE,
        defaults={
            'color': '#22c55e',   # グリーン（入門）
            'duration_days': 0,    # 有効期限なし
        }
    )

    # 全ユーザーのメタ情報を更新
    for meta in UserMeta.objects.all():
        earned = meta.earned_titles or []
        changed = False

        # 駆け出しクリエイターを付与
        if STARTER_TITLE not in earned:
            earned.append(STARTER_TITLE)
            meta.earned_titles = earned
            changed = True

        # アクティブ称号が未設定なら駆け出しクリエイターをセット
        if not meta.active_title:
            meta.active_title = STARTER_TITLE
            changed = True

        # 有効期限をクリア（廃止）
        if meta.expires_at is not None:
            meta.expires_at = None
            changed = True

        if changed:
            meta.save()


def revoke_starter_title(apps, schema_editor):
    """ロールバック用（earned_titles から削除するのみ）"""
    UserMeta = apps.get_model('users', 'UserMeta')
    for meta in UserMeta.objects.all():
        earned = meta.earned_titles or []
        if STARTER_TITLE in earned:
            earned.remove(STARTER_TITLE)
            meta.earned_titles = earned
            meta.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_usermeta_earned_titles'),
        ('gamification', '0004_add_card_fields_attribute_atk_def_type_buff'),
    ]

    operations = [
        migrations.RunPython(grant_starter_title, revoke_starter_title),
    ]
