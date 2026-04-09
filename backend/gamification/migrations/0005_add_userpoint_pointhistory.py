import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gamification", "0004_add_card_fields_attribute_atk_def_type_buff"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserPoint",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_points", models.PositiveIntegerField(default=0, verbose_name="累計ポイント")),
                ("migration_bonus_granted", models.BooleanField(default=False, verbose_name="移行ボーナス付与済み")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="point",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ユーザー",
                    ),
                ),
            ],
            options={
                "verbose_name": "ユーザーポイント",
                "verbose_name_plural": "ユーザーポイント",
                "db_table": "user_points",
            },
        ),
        migrations.CreateModel(
            name="PointHistory",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("registration_bonus", "初回登録ボーナス"),
                            ("migration_bonus", "移行ボーナス"),
                            ("daily_login", "毎日ログインボーナス"),
                            ("submission_image", "画像投稿"),
                            ("submission_video", "動画投稿"),
                            ("submission_game", "ゲーム投稿"),
                            ("reaction_received", "リアクション受取"),
                            ("game_played", "ゲームプレイされた"),
                        ],
                        max_length=50,
                        verbose_name="アクション種別",
                    ),
                ),
                ("points", models.IntegerField(verbose_name="ポイント数")),
                ("description", models.CharField(blank=True, max_length=200, verbose_name="説明")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="獲得日時")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="point_history",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="ユーザー",
                    ),
                ),
            ],
            options={
                "verbose_name": "ポイント履歴",
                "verbose_name_plural": "ポイント履歴",
                "db_table": "point_history",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["user", "-created_at"], name="point_hist_user_idx"),
                ],
            },
        ),
    ]
