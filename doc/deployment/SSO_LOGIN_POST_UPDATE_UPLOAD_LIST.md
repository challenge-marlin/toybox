# SSOログインPOST対応 - WinSCPアップロードファイルリスト

## 概要

StudySphere側から`/sso/login?ticket=xxx`にPOSTリクエストが来た場合の処理を実装しました。

## 実装内容

1. **`/sso/login/`エンドポイントの修正**
   - POSTリクエストを受け取れるように修正
   - クエリパラメータからチケットを取得
   - StudySphere側のSSO API（`https://backend.studysphere.ayatori-inc.co.jp/api/sso/ticket/verify`）にPOSTしてチケットを検証
   - アカウントがある場合：自動ログイン
   - アカウントがない場合：サインアップ画面にリダイレクト

2. **サインアップ画面の修正**
   - チケットパラメータからSSO情報を取得する処理を追加
   - チケットがある場合、自動的に検証してSSO情報を表示

## アップロードが必要なファイル

以下の2つのファイルをWinSCPでアップロードしてください。

### 1. バックエンド - SSOビュー
**ファイルパス**: `backend/sso_integration/views.py`  
**サーバー上のパス**: `/var/www/toybox/backend/sso_integration/views.py`  
**変更内容**: 
- `sso_login`をPOSTリクエストに対応
- `@csrf_exempt`デコレータを追加
- アカウントがない場合にサインアップ画面にリダイレクト
- `sso_callback`もアカウントがない場合にサインアップ画面にリダイレクト

### 2. フロントエンド - サインアップ画面
**ファイルパス**: `backend/frontend/templates/frontend/signup.html`  
**サーバー上のパス**: `/var/www/toybox/backend/frontend/templates/frontend/signup.html`  
**変更内容**: 
- チケットパラメータからSSO情報を取得する処理を追加
- `verifyTicketForSignup`関数を追加

## 環境変数の確認

以下の環境変数が正しく設定されているか確認してください：

```bash
# backend/.env または backend/env.prod
SSO_API_BASE_URL=https://backend.studysphere.ayatori-inc.co.jp
```

**重要**: `SSO_API_BASE_URL`が`https://backend.studysphere.ayatori-inc.co.jp`に設定されている必要があります。

## WinSCPでのアップロード手順

### ステップ1: WinSCPでサーバーに接続

1. WinSCPを起動
2. サーバーに接続（接続情報は`WINSCP_CONNECTION_INFO.md`を参照）

### ステップ2: ファイルをアップロード

左側（ローカル）から右側（サーバー）に、以下のファイルをドラッグ&ドロップでアップロード：

1. `backend/sso_integration/views.py` → `/var/www/toybox/backend/sso_integration/views.py`
2. `backend/frontend/templates/frontend/signup.html` → `/var/www/toybox/backend/frontend/templates/frontend/signup.html`

### ステップ3: 環境変数の確認

サーバー側で環境変数が正しく設定されているか確認：

```bash
cd /var/www/toybox/backend
docker compose exec web python manage.py shell
```

```python
from django.conf import settings
print("SSO_API_BASE_URL:", settings.SSO_API_BASE_URL)
```

`SSO_API_BASE_URL`が`https://backend.studysphere.ayatori-inc.co.jp`になっていることを確認してください。

### ステップ4: サーバー側でDjangoを再起動

```bash
docker compose restart web
docker compose logs web --tail=50
```

### ステップ5: 動作確認

1. StudySphere側から`https://toybox.ayatori-inc.co.jp/sso/login?ticket=xxx`にPOSTリクエストを送信
2. アカウントがある場合：
   - 自動ログインしてマイページにリダイレクトされることを確認
3. アカウントがない場合：
   - サインアップ画面（`/signup/?from=sso&ticket=xxx`）にリダイレクトされることを確認
   - IDフィールドに自動入力されていることを確認
   - パスワードフィールドが非表示になっていることを確認

## 動作フロー

1. **StudySphere側からPOSTリクエスト**
   ```
   POST https://toybox.ayatori-inc.co.jp/sso/login?ticket=xxx
   ```

2. **TOYBOX側でチケットを検証**
   - クエリパラメータからチケットを取得
   - `https://backend.studysphere.ayatori-inc.co.jp/api/sso/ticket/verify`にPOSTして検証

3. **アカウント存在チェック**
   - `studysphere_user_id`でTOYBOX側のユーザーを検索

4. **分岐処理**
   - **アカウントがある場合**: 自動ログインしてマイページにリダイレクト
   - **アカウントがない場合**: `/signup/?from=sso&ticket=xxx`にリダイレクト

5. **サインアップ画面での処理**
   - チケットパラメータからSSO情報を取得
   - IDフィールドに自動入力
   - パスワードフィールドは非表示
   - パスワードなしでアカウント作成可能

## トラブルシューティング

### エラー: "SSO API connection failed"

**原因**: `SSO_API_BASE_URL`が正しく設定されていない、またはネットワーク接続の問題

**解決方法**:
1. `SSO_API_BASE_URL`が`https://backend.studysphere.ayatori-inc.co.jp`になっているか確認
2. サーバーからStudySphereのAPIにアクセスできるか確認:
   ```bash
   docker compose exec web curl -X POST https://backend.studysphere.ayatori-inc.co.jp/api/sso/ticket/verify -H "Content-Type: application/json" -d '{"ticket":"test"}'
   ```

### エラー: "CSRF verification failed"

**原因**: CSRFトークンの検証エラー

**解決方法**:
- `@csrf_exempt`デコレータが正しく追加されているか確認
- ファイルを再アップロードして、Djangoを再起動

### エラー: "SSOチケットが見つかりませんでした"

**原因**: クエリパラメータからチケットが取得できていない

**解決方法**:
1. StudySphere側でリクエストURLに`?ticket=xxx`が含まれているか確認
2. サーバー側のログを確認:
   ```bash
   docker compose logs web --tail=100 | grep -i "sso login post"
   ```

## ファイル一覧（コピー用）

```
backend/sso_integration/views.py
backend/frontend/templates/frontend/signup.html
```

## 関連ドキュメント

- `STUDYSPHERE_SIDE_SETUP_INSTRUCTIONS.md` - StudySphere側への指示書
- `STUDYSPHERE_SSO_UPDATE_UPLOAD_LIST.md` - 以前の更新ファイルリスト
