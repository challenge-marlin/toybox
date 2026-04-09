from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_add_studysphere_fields'),
    ]

    operations = [
        # earned_titles フィールド追加
        migrations.AddField(
            model_name='usermeta',
            name='earned_titles',
            field=models.JSONField(blank=True, default=list, verbose_name='取得済み称号リスト'),
        ),
        # expires_at の help_text 更新（DB変更なし）
        migrations.AlterField(
            model_name='usermeta',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, help_text='v2.0以降は常にNULL（有効期限廃止）'),
        ),
    ]
