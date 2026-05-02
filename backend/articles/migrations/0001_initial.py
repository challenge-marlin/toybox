# Generated migration for articles app - Ver 2.20
from django.conf import settings
from django.db import migrations, models
import articles.models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='タイトル')),
                ('slug', models.SlugField(blank=True, max_length=250, unique=True)),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to=articles.models.article_thumbnail_upload, verbose_name='サムネイル')),
                ('thumbnail_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='サムネイルURL')),
                ('body', models.JSONField(blank=True, default=list, verbose_name='本文ブロック')),
                ('custom_css', models.TextField(blank=True, verbose_name='カスタムCSS')),
                ('status', models.CharField(choices=[('draft', '下書き'), ('published', '公開')], default='draft', max_length=20, verbose_name='ステータス')),
                ('published_at', models.DateTimeField(blank=True, null=True, verbose_name='公開日時')),
                ('pt_awarded', models.BooleanField(default=False, verbose_name='PT付与済み')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to=settings.AUTH_USER_MODEL, verbose_name='著者')),
            ],
            options={
                'verbose_name': '記事',
                'verbose_name_plural': '記事',
                'db_table': 'articles',
                'ordering': ['-published_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ArticleMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=articles.models.article_media_upload, verbose_name='ファイル')),
                ('media_type', models.CharField(choices=[('image', '画像'), ('video', '動画')], max_length=10, verbose_name='種別')),
                ('original_name', models.CharField(blank=True, max_length=255, verbose_name='元ファイル名')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('uploader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article_media', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '記事メディア',
                'verbose_name_plural': '記事メディア',
                'db_table': 'article_media',
            },
        ),
        migrations.CreateModel(
            name='ArticleReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('submit_medal', 'いいね！'), ('awesome', 'すごい！'), ('cute', 'かわいい！'), ('funny', '笑える！'), ('moved', '感動した'), ('cool', 'かっこいい！')], max_length=50, verbose_name='リアクションタイプ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='articles.article', verbose_name='記事')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article_reactions', to=settings.AUTH_USER_MODEL, verbose_name='ユーザー')),
            ],
            options={
                'verbose_name': '記事リアクション',
                'verbose_name_plural': '記事リアクション',
                'db_table': 'article_reactions',
            },
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['status', '-published_at'], name='articles_ar_status_pub_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['author', '-created_at'], name='articles_ar_author_ca_idx'),
        ),
        migrations.AddIndex(
            model_name='articlereaction',
            index=models.Index(fields=['article', 'type'], name='article_reactions_article_type_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='articlereaction',
            unique_together={('user', 'article', 'type')},
        ),
    ]
