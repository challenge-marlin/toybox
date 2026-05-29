# TOYBOX Ver 2.23 リリースお知らせ
from django.db import migrations

ANNOUNCEMENT_TITLE = 'TOYBOX! Ver 2.23 アップデートのお知らせ'

ANNOUNCEMENT_CONTENT = """TOYBOX! を Ver 2.23 にアップデートしました。
いつもご利用ありがとうございます。主な変更点は以下のとおりです。

■ ブックマーク機能
・リポスト機能を廃止し、気に入った作品をブックマークできるようになりました。
・マイページ・プロフィールからブックマーク一覧を確認できます。
・自分の投稿はブックマークできません。

■ リアクションの追加
・新しいリアクションを3種類追加しました。
  ✨ きれい（3 TP）／ 🥹 エモい！（5 TP）／ 🎮 神ゲー（10 TP）

■ 称号の追加
・上記リアクションに対応した称号を多数追加しました。
  ・入門〜中級：各リアクションごとに段階的に獲得できます
  ・上級・伝説：高い獲得数で挑戦できる秘密称号
  ・超越：さらに上のティア。獲得すると称号バッジとアイコンがネオン演出になります（未獲得時は他の秘密称号と同様、条件は非公開です）

■ 通知まわり
・リアクションなどの通知をタップすると、該当する作品画面へ移動します。

■ ランキング・プロフィール
・「みんなの投稿」のデイリー／週間ランキングで、順位をカードの外側に表示するようになりました。
・プロフィールに「記事」「ブックマーク」を追加し、投稿一覧より上に表示するようになりました（見つけやすくなります）。
・プロフィールの「提出一覧」を「投稿一覧」に名称変更しました。
・プロフィールに記事一覧を表示できるようになりました（StudySphere 連携アカウント対応）。
・マイページのランキング入賞バッジを、ライトモードでも見やすいデザインに改善しました。

■ その他の改善
・ハッシュタグ検索時に、関係のない記事が混ざる不具合を修正しました。
・投稿者リストの表示を改善しました（「投稿した人」）。
・記事・投稿の表示名を、ユーザーIDではなく表示名優先に統一しました。
・画面右下に「ページトップへ戻る」ボタンを追加しました。
・フッターのロゴからマイページへ移動できるようになりました。

今後とも TOYBOX! をよろしくお願いいたします。"""


def create_v223_announcement(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    if Announcement.objects.filter(title=ANNOUNCEMENT_TITLE).exists():
        return
    Announcement.objects.create(
        title=ANNOUNCEMENT_TITLE,
        content=ANNOUNCEMENT_CONTENT,
        is_active=True,
    )


def remove_v223_announcement(apps, schema_editor):
    Announcement = apps.get_model('frontend', 'Announcement')
    Announcement.objects.filter(title=ANNOUNCEMENT_TITLE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0003_fix_site_maintenance_sequence'),
    ]

    operations = [
        migrations.RunPython(create_v223_announcement, remove_v223_announcement),
    ]
