# StudySphere SSO設定ガイド

## 概要

TOYBOXとStudySphereのSSO連携を設定するためのガイドです。この連携により、StudySphereのユーザーがTOYBOXにシームレスにログインできるようになります。

## 必要な設定項目

StudySphere SSO連携には以下の環境変数の設定が必要です：

```bash
# StudySphere SSO設定
SSO_HUB_BASE_URL=https://studysphere-hub.example.com  # SSO HubのベースURL（オプション）
SSO_API_BASE_URL=https://studysphere-api.example.com  # SSO APIのベースURL
SSO_WEB_BASE_URL=https://studysphere.example.com      # StudySphere WebのベースURL
SSO_SYSTEM_KEY=toybox_prod                            # TOYBOXのシステムキー（StudySphere側で登録された値）
SSO_SERVICE_TOKEN=your_service_token_here             # StudySphereから提供されるサービストークン
```

## 1. StudySphere側での設定

### 1.1 システム登録

StudySphereのSSO管理画面で、TOYBOXを連携システムとして登録する必要があります。以下の情報をStudySphere側に提供してください：

- **システムキー**: `toybox_prod`（または開発環境の場合は`toybox_dev`）
- **コールバックURL**: `https://yourdomain.com/api/sso/callback/`
- **システム名**: TOYBOX

### 1.2 サービストークンの取得

`SSO_SERVICE_TOKEN`は、StudySphere側の管理者から提供される認証トークンです。このトークンは以下の用途で使用されます：

- StudySphereのSSO APIへの認証
- チケット生成API（`/api/sso/ticket/generate`）へのアクセス

**取得方法**:
1. StudySphereの管理者に連絡
2. TOYBOXシステムの登録を依頼
3. サービストークン（`SSO_SERVICE_TOKEN`）の発行を依頼

**重要**: 
- このトークンは機密情報です。環境変数や`.env`ファイルに保存し、Gitリポジトリにはコミットしないでください
- 本番環境と開発環境で異なるトークンが発行される場合があります

## 2. 環境変数の設定

### 2.1 `.env`ファイルの設定

`backend/.env`ファイル（または`backend/env.prod`ファイル）に以下の設定を追加します：

```bash
# StudySphere SSO
SSO_HUB_BASE_URL=https://studysphere-hub.ayatori-inc.co.jp
SSO_API_BASE_URL=https://studysphere-api.ayatori-inc.co.jp
SSO_WEB_BASE_URL=https://studysphere.ayatori-inc.co.jp
SSO_SYSTEM_KEY=toybox_prod
SSO_SERVICE_TOKEN=ここにStudySphereから提供されたトークンを設定
```

### 2.2 環境変数の確認

設定が正しく読み込まれているか確認するには：

```bash
# Dockerコンテナ内で確認
docker compose exec web python manage.py shell
```

```python
from django.conf import settings
print("SSO_API_BASE_URL:", settings.SSO_API_BASE_URL)
print("SSO_SYSTEM_KEY:", settings.SSO_SYSTEM_KEY)
print("SSO_SERVICE_TOKEN:", settings.SSO_SERVICE_TOKEN[:10] + "..." if settings.SSO_SERVICE_TOKEN else "未設定")
```

## 3. SSO連携の動作確認

### 3.1 チケット検証の確認

StudySphereからリダイレクトされた際のチケット検証が正常に動作するか確認：

1. StudySphereからTOYBOXにリダイレクトされる
2. URLパラメータに`ticket`が含まれる（例: `?ticket=xxx`）
3. `/api/sso/callback/`エンドポイントでチケットが検証される
4. ユーザーが自動的にログインまたはアカウント作成される

### 3.2 ログの確認

SSO連携時のログを確認：

```bash
docker compose logs web | grep -i sso
```

正常な場合のログ例：
```
INFO: Authenticated user via SSO: username (studysphere_id=12345)
INFO: Created user via SSO: username (studysphere_id=12345)
```

エラーの場合のログ例：
```
ERROR: SSO API error: 401
ERROR: Missing setting: SSO_SERVICE_TOKEN
ERROR: SSO ticket invalid: xxx
```

## 4. よくあるエラーと解決方法

### 4.1 "Missing setting: SSO_SERVICE_TOKEN"

**原因**: 環境変数`SSO_SERVICE_TOKEN`が設定されていない

**解決方法**:
1. `.env`ファイルに`SSO_SERVICE_TOKEN`を追加
2. Dockerコンテナを再起動: `docker compose restart web`

### 4.2 "SSO API error: 401"

**原因**: `SSO_SERVICE_TOKEN`が無効または期限切れ

**解決方法**:
1. StudySphere側の管理者に連絡してトークンの有効性を確認
2. 必要に応じて新しいトークンを取得して更新

### 4.3 "SSO API connection failed"

**原因**: `SSO_API_BASE_URL`が正しく設定されていない、またはネットワーク接続の問題

**解決方法**:
1. `SSO_API_BASE_URL`が正しいURLか確認
2. サーバーからStudySphereのAPIにアクセスできるか確認:
   ```bash
   curl https://studysphere-api.example.com/api/sso/ticket/verify
   ```

### 4.4 "SSO ticket invalid"

**原因**: 
- チケットが期限切れ
- チケットが既に使用済み
- StudySphere側の設定が正しくない

**解決方法**:
1. StudySphere側のチケット有効期限設定を確認
2. 新しいチケットで再試行
3. StudySphere側の管理者に連絡

## 5. セキュリティに関する注意事項

1. **トークンの管理**:
   - `SSO_SERVICE_TOKEN`は機密情報です
   - `.env`ファイルを`.gitignore`に追加してGitにコミットしないようにする
   - 本番環境では環境変数として直接設定することを推奨

2. **HTTPSの使用**:
   - 本番環境では必ずHTTPSを使用してください
   - `SSO_API_BASE_URL`と`SSO_WEB_BASE_URL`は`https://`で始まる必要があります

3. **システムキーの管理**:
   - `SSO_SYSTEM_KEY`はStudySphere側で登録された値と一致させる必要があります
   - 開発環境と本番環境で異なる値を設定することを推奨

## 6. 参考情報

### 使用されているAPIエンドポイント

- `/api/sso/ticket/verify`: チケットの検証
- `/api/sso/ticket/generate`: チケットの生成（`SSO_SERVICE_TOKEN`が必要）
- `/api/sso/ticket/generate-by-logincode`: ログインコードからチケットを生成

### 関連ファイル

- `backend/sso_integration/services.py`: SSO APIとの通信処理
- `backend/sso_integration/views.py`: SSO関連のビュー
- `backend/sso_integration/backends.py`: StudySphere認証バックエンド
- `backend/toybox/settings/base.py`: SSO設定の読み込み

## 7. サポート

問題が解決しない場合は、以下を確認してください：

1. StudySphere側の管理者に連絡して、システム登録とトークン発行の状況を確認
2. ログファイルを確認してエラーの詳細を把握
3. ネットワーク接続とファイアウォール設定を確認
