# Generated manually for card master new fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gamification", "0003_title_image_title_image_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="card",
            name="description",
            field=models.TextField(blank=True, null=True, verbose_name="カード説明"),
        ),
        migrations.AddField(
            model_name="card",
            name="attribute",
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name="属性"),
        ),
        migrations.AddField(
            model_name="card",
            name="atk_points",
            field=models.IntegerField(blank=True, null=True, verbose_name="ATKポイント"),
        ),
        migrations.AddField(
            model_name="card",
            name="def_points",
            field=models.IntegerField(blank=True, null=True, verbose_name="DEFポイント"),
        ),
        migrations.AddField(
            model_name="card",
            name="card_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("character", "キャラクターカード"),
                    ("effect", "エフェクトカード"),
                ],
                help_text="キャラクターカードかエフェクトカードか",
                max_length=20,
                null=True,
                verbose_name="カード種別",
            ),
        ),
        migrations.AddField(
            model_name="card",
            name="buff_effect",
            field=models.TextField(blank=True, null=True, verbose_name="バフ効果"),
        ),
    ]
