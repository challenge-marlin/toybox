from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Reaction.Type に5種類のポジティブリアクションを追加。
    choices の変更のみで DB スキーマ変更なし（varchar のまま）。
    """

    dependencies = [
        ('submissions', '0004_submission_thumbnail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reaction',
            name='type',
            field=models.CharField(
                choices=[
                    ('submit_medal', 'いいね！'),
                    ('awesome', 'すごい！'),
                    ('cute', 'かわいい！'),
                    ('funny', '笑える！'),
                    ('moved', '感動した'),
                    ('cool', 'かっこいい！'),
                ],
                max_length=50,
                verbose_name='リアクションタイプ',
            ),
        ),
    ]
