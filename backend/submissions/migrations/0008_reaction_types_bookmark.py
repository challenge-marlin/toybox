# Generated manually: 新リアクション3種の追加 + SubmissionBookmark

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('submissions', '0007_submissionrepost'),
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
                    ('beautiful', 'きれい'),
                    ('emotional', 'エモい！'),
                    ('god_game', '神ゲー！'),
                ],
                max_length=50,
                verbose_name='リアクションタイプ',
            ),
        ),
        migrations.CreateModel(
            name='SubmissionBookmark',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmarks', to='submissions.submission', verbose_name='投稿')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submission_bookmarks', to=settings.AUTH_USER_MODEL, verbose_name='ブックマークしたユーザー')),
            ],
            options={
                'db_table': 'submission_bookmarks',
                'verbose_name': 'ブックマーク',
                'verbose_name_plural': 'ブックマーク',
            },
        ),
        migrations.AddConstraint(
            model_name='submissionbookmark',
            constraint=models.UniqueConstraint(fields=('user', 'submission'), name='uniq_submission_bookmark_user_submission'),
        ),
        migrations.AddIndex(
            model_name='submissionbookmark',
            index=models.Index(fields=['user', '-created_at'], name='submbm_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='submissionbookmark',
            index=models.Index(fields=['submission', '-created_at'], name='submbm_sub_created_idx'),
        ),
    ]
