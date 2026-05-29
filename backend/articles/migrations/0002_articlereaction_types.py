# Generated manually: 記事リアクションに新3種を追加（choices変更のみ）

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articlereaction',
            name='type',
            field=models.CharField(
                choices=[
                    ('submit_medal', 'いいね！'),
                    ('awesome', 'すごい！'),
                    ('cute', 'かわいい！'),
                    ('funny', '笑える！'),
                    ('moved', '感動した'),
                    ('cool', 'かっこいい！'),
                    ('beautiful', 'きれい'),
                    ('emotional', 'エモい！'),
                    ('god_game', '神ゲー！'),
                ],
                max_length=50,
                verbose_name='リアクションタイプ',
            ),
        ),
    ]
