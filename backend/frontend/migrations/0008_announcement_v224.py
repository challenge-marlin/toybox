# TOYBOX Ver 2.24 リリースお知らせ
from django.db import migrations

ANNOUNCEMENT_TITLE = 'TOYBOX! Ver 2.24 アップデートのお知らせ'

ANNOUNCEMENT_CONTENT = """TOYBOX! を Ver 2.24 にアップデートしました。
いつもご利用ありがとうございます。主な変更点は以下のとおりです。

■ ランキング表示の改善
・マイページ・プロフィールに表示される「週間／デイリーランキング第〇位」が、自分の順位を正しく表示するようになりました。
・ランキング集計を見直し、期間外の古い投稿が混入したり、同一ユーザーが重複表示されたりする問題を修正しました。
・集計リセット直後に「データなし」になりにくく、週間ランキングは先週分を表示するフォールバックを追加しました。
・1時間ごとに順位を再集計し、表示のズレを抑えるようにしました。

■ 「投稿した人（当日）」の表示修正
・当日投稿済みなのに一覧に表示されないことがあった問題を修正しました。
・日本時間（JST）基準で「当日」を判定するように変更しました。

■ サムネイル表示の改善
・タイムラインや新着投稿で、動画・ゲームのサムネイルが表示されないことがあった問題を修正しました。
・動画は先頭フレーム、ゲームは設定したサムネイル画像を表示します。

■ 自分の投稿を削除できる機能を追加
・マイページのタイムライン、および自分のプロフィールページから、自分の投稿のみ削除できるようになりました。
・他人の投稿には削除ボタンは表示されません。
・削除前に確認ダイアログを表示します。

■ アップロード上限の引き上げ
・動画ファイル：最大 200MB
・ゲームZIPファイル：最大 200MB（従来 50MB）
・アップロード画面にも上限の説明を追記しました。
・大容量ファイルのアップロードが途中で切れないよう、サーバー側のタイムアウト設定も調整しています。

■ ゲームアップロードの不具合修正
・ゲームZIPをアップロードした際に「処理に失敗しました」と表示される問題を修正しました。

今後とも TOYBOX! をよろしくお願いいたします。"""


def create_v224_announcement(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    if Announcement.objects.filter(title=ANNOUNCEMENT_TITLE).exists():
        return
    Announcement.objects.create(
        title=ANNOUNCEMENT_TITLE,
        content=ANNOUNCEMENT_CONTENT,
        is_active=True,
    )


def remove_v224_announcement(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    Announcement.objects.filter(title=ANNOUNCEMENT_TITLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0007_update_v223_announcement_full'),
    ]

    operations = [
        migrations.RunPython(create_v224_announcement, remove_v224_announcement),
    ]
