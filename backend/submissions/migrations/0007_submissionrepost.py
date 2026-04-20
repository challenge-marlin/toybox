# Generated manually for SubmissionRepost

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('submissions', '0006_submission_ai_tool_submission_spell'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionRepost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reposts', to='submissions.submission', verbose_name='投稿')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submission_reposts', to=settings.AUTH_USER_MODEL, verbose_name='リポストしたユーザー')),
            ],
            options={
                'db_table': 'submission_reposts',
                'verbose_name': 'リポスト',
                'verbose_name_plural': 'リポスト',
            },
        ),
        migrations.AddConstraint(
            model_name='submissionrepost',
            constraint=models.UniqueConstraint(fields=('user', 'submission'), name='uniq_submission_repost_user_submission'),
        ),
        migrations.AddIndex(
            model_name='submissionrepost',
            index=models.Index(fields=['submission', '-created_at'], name='submrepost_sub_created_idx'),
        ),
    ]
