# Generated manually for TOYBOX Ver 2.10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0005_add_reaction_types_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='spell',
            field=models.TextField(blank=True, help_text='任意。投稿の拡大表示などで表示されます。', verbose_name='呪文（プロンプト）'),
        ),
        migrations.AddField(
            model_name='submission',
            name='ai_tool',
            field=models.CharField(blank=True, db_index=True, help_text='定義済みキー（chatgpt 等）。未選択は空文字。', max_length=64, verbose_name='使用した生成AI'),
        ),
    ]
