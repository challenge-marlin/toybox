# StudySphere SSO連携更新 - WinSCPアップロードファイルリスト

## 概要

StudySphereからの連携で、パスワードなしでログイン・登録できるようにする機能を追加しました。

## アップロードが必要なファイル

以下の6つのファイルをWinSCPでアップロードしてください。

### 1. バックエンド - シリアライザー
**ファイルパス**: `backend/users/serializers.py`  
**サーバー上のパス**: `/var/www/toybox/backend/users/serializers.py`  
**変更内容**: SSO経由の登録でパスワードをオプションに変更

### 2. バックエンド - SSOビュー
**ファイルパス**: `backend/sso_integration/views.py`  
**サーバー上のパス**: `/var/www/toybox/backend/sso_integration/views.py`  
**変更内容**: 
- `sso_verify_and_check`に`sso_data`を追加
- `sso_login_with_ticket`エンドポイントを追加（IDとチケットでログイン）

### 3. バックエンド - SSO URL設定
**ファイルパス**: `backend/sso_integration/urls.py`  
**サーバー上のパス**: `/var/www/toybox/backend/sso_integration/urls.py`  
**変更内容**: `/sso/login-with-ticket/`エンドポイントを追加

### 4. フロントエンド - ログイン画面
**ファイルパス**: `backend/frontend/templates/frontend/login.html`  
**サーバー上のパス**: `/var/www/toybox/backend/frontend/templates/frontend/login.html`  
**変更内容**: 
- SSO経由の場合、IDフィールドに自動入力
- パスワードなしでログイン可能に

### 5. フロントエンド - 登録画面
**ファイルパス**: `backend/frontend/templates/frontend/signup.html`  
**サーバー上のパス**: `/var/www/toybox/backend/frontend/templates/frontend/signup.html`  
**変更内容**: 
- SSO経由の場合、パスワードフィールドを非表示
- パスワードなしでアカウント作成可能に

### 6. StudySphere側への指示書（参考用）
**ファイルパス**: `STUDYSPHERE_SIDE_SETUP_INSTRUCTIONS.md`  
**サーバー上のパス**: アップロード不要（StudySphere側に渡すためのドキュメント）  
**変更内容**: 
- StudySphere側の実装指示書
- SSOディスパッチエンドポイントの実装方法を記載

## WinSCPでのアップロード手順

### ステップ1: WinSCPでサーバーに接続

1. WinSCPを起動
2. サーバーに接続（接続情報は`WINSCP_CONNECTION_INFO.md`を参照）

### ステップ2: ファイルをアップロード

左側（ローカル）から右側（サーバー）に、以下のファイルをドラッグ&ドロップでアップロード：

1. `backend/users/serializers.py` → `/var/www/toybox/backend/users/serializers.py`
2. `backend/sso_integration/views.py` → `/var/www/toybox/backend/sso_integration/views.py` ⚠️ **重要**: `sso_callback`を修正してアカウントがない場合もチケットを保持
3. `backend/sso_integration/urls.py` → `/var/www/toybox/backend/sso_integration/urls.py`
4. `backend/frontend/templates/frontend/login.html` → `/var/www/toybox/backend/frontend/templates/frontend/login.html`
5. `backend/frontend/templates/frontend/signup.html` → `/var/www/toybox/backend/frontend/templates/frontend/signup.html`

**注意**: 
- 既存のファイルを上書きするか確認されますが、「はい」を選択してください
- ファイルのパーミッションは自動的に保持されます

### ステップ3: サーバー側でDjangoを再起動

WinSCPのターミナル機能を使用するか、SSH接続で：

```bash
# Dockerコンテナを再起動
cd /var/www/toybox/backend
docker compose restart web

# または、特定のコンテナのみ再起動
docker compose restart web

# ログを確認
docker compose logs web --tail=50
```

### ステップ4: 動作確認

1. StudySphereにログイン
2. 「TOYBOXへ」ボタンをクリック
3. チケット付きでTOYBOXのログイン画面にリダイレクトされることを確認
4. アカウントがある場合:
   - IDフィールドに自動入力されていることを確認
   - パスワードフィールドが「不要」と表示されていることを確認
   - 「ログイン」ボタンでパスワードなしでログインできることを確認
5. アカウントがない場合:
   - 登録画面にリダイレクトされることを確認
   - IDフィールドに自動入力されていることを確認
   - パスワードフィールドが非表示になっていることを確認
   - 「作成」ボタンでパスワードなしでアカウント作成できることを確認

## トラブルシューティング

### エラー: "ModuleNotFoundError: No module named 'sso_integration'"

**原因**: Pythonパスの問題またはモジュールが見つからない

**解決方法**:
```bash
# Dockerコンテナ内で確認
docker compose exec web python manage.py check
```

### エラー: "404 Not Found" (ログイン画面で)

**原因**: URLルーティングが正しく設定されていない

**解決方法**:
```bash
# URL設定を確認
docker compose exec web python manage.py show_urls | grep sso
```

### エラー: "パスワードは必須です" (登録時)

**原因**: シリアライザーの変更が反映されていない

**解決方法**:
```bash
# Dockerコンテナを再起動
docker compose restart web

# ログを確認
docker compose logs web --tail=100
```

### ファイルが見つからない

**原因**: ファイルパスが間違っている

**解決方法**:
- WinSCPでサーバー側のディレクトリ構造を確認
- 正しいパスにアップロードされているか確認

## ファイル一覧（コピー用）

```
backend/users/serializers.py
backend/sso_integration/views.py
backend/sso_integration/urls.py
backend/frontend/templates/frontend/login.html
backend/frontend/templates/frontend/signup.html
```

## StudySphere側への指示書

`STUDYSPHERE_SIDE_SETUP_INSTRUCTIONS.md`をStudySphere側の開発チームに渡してください。このファイルには、StudySphere側で実装が必要な内容が記載されています。

## 関連ドキュメント

- `STUDYSPHERE_SSO_SETUP.md` - StudySphere SSO設定ガイド
- `WINSCP_CONNECTION_INFO.md` - WinSCP接続情報
- `WINSCP_DEPLOYMENT_GUIDE.md` - WinSCPでのデプロイ手順
