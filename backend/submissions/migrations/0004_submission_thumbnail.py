# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0003_alter_reaction_options_alter_submission_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='thumbnail',
            field=models.ImageField(blank=True, help_text='ゲーム提出時のサムネイル画像', null=True, upload_to='submissions/thumbnails/', verbose_name='サムネイル'),
        ),
    ]
















