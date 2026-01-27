# TOYBOX画像配信システム リファクタリング - WinSCPアップロードリスト

## 概要
画像配信の問題を根本的に解決するため、設定ファイルを整理・統一しました。

## WinSCPでアップロードするファイル（合計8ファイル）

### 1. Caddyfile（緊急修正：サイト復旧のため）
- **ローカルパス**: `c:\github\toybox\Caddyfile`
- **サーバーパス**: `/var/www/toybox/Caddyfile`
- **変更内容**: `/uploads/*`をDjango経由（`reverse_proxy web:8000`）に戻してサイトを復旧

### 2. backend/toybox/media.py
- **ローカルパス**: `c:\github\toybox\backend\toybox\media.py`
- **サーバーパス**: `/var/www/toybox/backend/toybox/media.py`
- **変更内容**: 本番環境でも画像配信URLパターンを追加、Path変換対応

### 3. backend/users/views.py
- **ローカルパス**: `c:\github\toybox\backend\users\views.py`
- **サーバーパス**: `/var/www/toybox/backend/users/views.py`
- **変更内容**: ファイルの存在確認を削除、デバッグログを追加

### 4. backend/users/serializers.py
- **ローカルパス**: `c:\github\toybox\backend\users\serializers.py`
- **サーバーパス**: `/var/www/toybox/backend/users/serializers.py`
- **変更内容**: ファイルの存在確認を削除、デバッグログを追加

### 4-1. backend/users/views.py（追加修正）
- **ローカルパス**: `c:\github\toybox\backend\users\views.py`
- **サーバーパス**: `/var/www/toybox/backend/users/views.py`
- **変更内容**: デバッグログを追加

### 4-2. backend/frontend/templates/frontend/me.html（新規追加）
- **ローカルパス**: `c:\github\toybox\backend\frontend\templates\frontend\me.html`
- **サーバーパス**: `/var/www/toybox/backend/frontend/templates/frontend/me.html`
- **変更内容**: プロフィール画像のデバッグログを追加

### 4-3. backend/frontend/templates/frontend/profile_view.html（新規追加）
- **ローカルパス**: `c:\github\toybox\backend\frontend\templates\frontend\profile_view.html`
- **サーバーパス**: `/var/www/toybox/backend/frontend/templates/frontend/profile_view.html`
- **変更内容**: プロフィール画像のデバッグログを追加

### 4-4. backend/frontend/templates/frontend/base.html（新規追加）
- **ローカルパス**: `c:\github\toybox\backend\frontend\templates\frontend\base.html`
- **サーバーパス**: `/var/www/toybox/backend/frontend/templates/frontend/base.html`
- **変更内容**: ヘッダーアバター画像のデバッグログを追加

### 5. backend/toybox/image_utils.py（重要：修正追加）
- **ローカルパス**: `c:\github\toybox\backend\toybox\image_utils.py`
- **サーバーパス**: `/var/www/toybox/backend/toybox/image_utils.py`
- **変更内容**: 
  - `_get_file_path_from_url`で`MEDIA_ROOT`を`Path`オブジェクトに変換（文字列エラー回避）
  - `get_image_url`で`request`が`None`の場合でも絶対URLを返すように修正（`settings.MEDIA_URL`を使用）

### 6. backend/toybox/settings/prod.py
- **ローカルパス**: `c:\github\toybox\backend\toybox\settings\prod.py`
- **サーバーパス**: `/var/www/toybox/backend/toybox/settings/prod.py`
- **変更内容**: `MEDIA_ROOT`を`public/uploads`に修正（実際のファイルパスに合わせる）

### 8. docker-compose.prod.yml（既にアップロード済みの場合は不要）
- **ローカルパス**: `c:\github\toybox\docker-compose.prod.yml`
- **サーバーパス**: `/var/www/toybox/docker-compose.prod.yml`
- **変更内容**: uploadsディレクトリのマウント設定

---

## アップロード後の実行コマンド

**サーバー上で以下を一度に実行してください：**

```bash
cd /var/www/toybox/backend && docker compose restart web && sleep 5 && cd /var/www/toybox && docker compose -f docker-compose.prod.yml restart caddy && sleep 3 && echo "=== Webサービス確認 ===" && docker compose ps | grep web && echo "=== Caddy確認 ===" && docker compose -f docker-compose.prod.yml ps | grep caddy && echo "=== サイトアクセステスト ===" && curl -I https://toybox.ayatori-inc.co.jp | head -5
```

---

## 変更内容の詳細

### 1. Caddyfile
- `/uploads/*`をDjango（web:8000）に転送
- 画像はDjango経由で配信（確実に動作）

### 2. backend/toybox/media.py
- 本番環境でも画像配信URLパターンを追加
- `Path`オブジェクトに変換してからパス操作（文字列エラー回避）
- 以下のパスに対応：
  - `/uploads/cards/*`
  - `/uploads/titles/*`
  - `/uploads/submissions/*`
  - `/uploads/profiles/*`
  - `/uploads/games/*`
  - `/uploads/*`（フォールバック）
  - `/media/*`（互換性）

### 3. backend/users/views.py
- `ProfileGetView`でファイルの存在確認を削除
- アバターURLとヘッダーURLをそのまま返すように変更
- デバッグログを追加（データベースから取得したURLをログ出力）

### 4. backend/users/serializers.py
- `UserMetaSerializer`でファイルの存在確認を削除
- アバターURLとヘッダーURLをそのまま返すように変更
- デバッグログを追加（データベースから取得したURLと`get_image_url`後のURLをログ出力）

### 4-1〜4-4. フロントエンドテンプレート（me.html, profile_view.html, base.html）
- プロフィール画像関連のデバッグログを追加
- APIレスポンス、画像URL、画像読み込みエラーをコンソールに出力

### 5. backend/toybox/image_utils.py
- `_get_file_path_from_url`で`settings.MEDIA_ROOT`を`Path`オブジェクトに変換
- 画像URLからファイルパスを取得する際の文字列エラーを回避

### 6. backend/toybox/settings/prod.py
- `MEDIA_ROOT`を`media`から`public/uploads`に変更
- 実際のファイルパスと一致させる

### 7. docker-compose.prod.yml
- `./backend/public/uploads:/app/public/uploads:ro`をマウント
- Caddyコンテナからファイルにアクセス可能（将来の直接配信用）

---

## 動作確認

### 1. サイトが正常に動作しているか確認
```bash
curl -I https://toybox.ayatori-inc.co.jp
```
**期待結果**: `HTTP/2 200`

### 2. 画像が表示されるか確認
ブラウザで以下にアクセス：
- `https://toybox.ayatori-inc.co.jp/uploads/profiles/avatar_10_321840f5.png`
- `https://toybox.ayatori-inc.co.jp/uploads/submissions/16_1768823957.png`

### 3. エラーログ確認（問題がある場合）
```bash
cd /var/www/toybox/backend && docker compose logs web | tail -50
cd /var/www/toybox && docker compose -f docker-compose.prod.yml logs caddy | tail -50
```

---

## トラブルシューティング

### 500エラーが出る場合
1. `backend/toybox/media.py`が正しくアップロードされているか確認
2. `backend/toybox/settings/prod.py`が正しくアップロードされているか確認
3. webサービスのログを確認：`docker compose logs web | tail -50`

### 画像が404エラーになる場合
1. ファイルが存在するか確認：`ls -la /var/www/toybox/backend/public/uploads/profiles/`
2. Django側で画像配信が有効か確認：`docker compose logs web | grep "uploads"`
3. ブラウザの開発者ツール（F12）で実際のリクエストURLを確認

### サイトにアクセスできない場合
1. Caddyが起動しているか確認：`docker compose -f docker-compose.prod.yml ps`
2. webサービスが起動しているか確認：`cd /var/www/toybox/backend && docker compose ps`
3. ポート80/443が使用されているか確認：`ss -tlnp | grep -E ':80|:443'`

---

## 今後の改善案

現在はDjango経由で画像を配信していますが、パフォーマンス向上のため、将来的にCaddyで直接配信する設定に変更することも可能です。

その場合は、Caddyfileを以下のように変更します：
```caddy
handle_path /uploads/* {
    root * /app/public/uploads
    file_server
}
```

ただし、現在の設定（Django経由）でも正常に動作します。
