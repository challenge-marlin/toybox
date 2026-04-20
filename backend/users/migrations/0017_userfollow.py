# Generated manually for TOYBOX Ver 2.10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_grant_starter_title'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFollow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('follower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='following_links', to=settings.AUTH_USER_MODEL, verbose_name='フォローする人')),
                ('following', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follower_links', to=settings.AUTH_USER_MODEL, verbose_name='フォローされる人')),
            ],
            options={
                'verbose_name': 'ユーザーフォロー',
                'verbose_name_plural': 'ユーザーフォロー',
                'db_table': 'user_follows',
            },
        ),
        migrations.AddConstraint(
            model_name='userfollow',
            constraint=models.UniqueConstraint(fields=('follower', 'following'), name='uniq_user_follow_pair'),
        ),
        migrations.AddIndex(
            model_name='userfollow',
            index=models.Index(fields=['follower'], name='user_follows_follower_idx'),
        ),
        migrations.AddIndex(
            model_name='userfollow',
            index=models.Index(fields=['following'], name='user_follows_following_idx'),
        ),
    ]
