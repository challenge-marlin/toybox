# SSO処理中の502 Bad Gatewayエラー解決手順

## 問題の概要
TOYBOXのSSO処理中に「502 Bad Gateway nginx/1.24.0 (Ubuntu)」エラーが発生し、接続できない状態。

## 原因の可能性
1. **Djangoアプリケーション（webサービス）が起動していない、またはクラッシュしている**
2. **nginxがDjangoアプリケーションに接続できない**（Dockerネットワークの問題）
3. **SSO処理の外部API呼び出しでタイムアウトが発生している**
4. **システムレベルのnginxが動いていて、Dockerコンテナのwebサービスに接続できていない**

## 実施した修正

### 1. SSO処理のタイムアウトを延長
- **ファイル**: `backend/sso_integration/services.py`
- **変更**: `DEFAULT_TIMEOUT_SECONDS` を 5秒 → 30秒に延長
- **理由**: 外部API呼び出しが5秒でタイムアウトしていた可能性がある

### 2. nginx設定のタイムアウトを延長
- **ファイル**: `backend/nginx/conf/default.conf`
- **変更**: `proxy_read_timeout` を 60秒 → 90秒に延長
- **理由**: SSO処理に時間がかかる場合に対応

### 3. SSO処理のエラーハンドリングを改善
- **ファイル**: `backend/sso_integration/views.py`
- **変更**: 
  - すべての例外をキャッチして適切に処理
  - より詳細なログを記録（`logger.error`、`logger.exception`）
  - ユーザーに適切なエラーメッセージを表示

### 4. SSOサービス層のエラーハンドリングを改善
- **ファイル**: `backend/sso_integration/services.py`
- **変更**:
  - タイムアウトエラーと接続エラーを個別に処理
  - より詳細なログを記録

## サーバー上での診断手順

### ステップ1: Dockerコンテナの状態を確認

```bash
# プロジェクトディレクトリに移動
cd /path/to/toybox/backend

# Dockerコンテナの状態を確認
docker compose ps

# webサービス（Djangoアプリケーション）のログを確認
docker compose logs web --tail=100

# webサービスが起動しているか確認
docker compose logs web | grep -i "error\|exception\|started"
```

### ステップ2: nginxの状態を確認

```bash
# システムレベルのnginxが動いているか確認
sudo systemctl status nginx

# nginxプロセスを確認
ps aux | grep nginx

# ポート80/443が使用されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
# または
sudo ss -tlnp | grep -E ':80|:443'
```

### ステップ3: Dockerネットワークを確認

```bash
# Dockerネットワークを確認
docker network ls

# webサービスがネットワークに接続されているか確認
docker network inspect backend_default | grep web

# webサービスに直接接続テスト
docker compose exec web curl http://localhost:8000/api/health/
```

### ステップ4: SSO処理のログを確認

```bash
# Djangoアプリケーションのログを確認（SSO関連）
docker compose logs web | grep -i "sso\|SSO"

# エラーログを確認
docker compose logs web | grep -i "error\|exception\|timeout"
```

## 解決手順

### 方法A: Dockerコンテナを再起動（推奨）

```bash
# プロジェクトディレクトリに移動
cd /path/to/toybox/backend

# コンテナを停止
docker compose down

# コンテナを再起動
docker compose up -d --build

# コンテナの状態を確認
docker compose ps

# ログを確認
docker compose logs -f web
```

### 方法B: システムレベルのnginxを停止

```bash
# nginxを停止
sudo systemctl stop nginx

# nginxを無効化（再起動時に自動起動しないようにする）
sudo systemctl disable nginx

# 確認
sudo systemctl status nginx
```

### 方法C: nginxサービスをDockerコンテナに追加（推奨）

`backend/docker-compose.yml`にnginxサービスを追加する場合：

```yaml
services:
  # ... 既存のサービス ...

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf/default.conf:/etc/nginx/conf.d/default.conf:ro
      - static_volume:/app/staticfiles:ro
    depends_on:
      - web
    restart: unless-stopped
```

その後、コンテナを再起動：

```bash
docker compose up -d --build
```

## 確認事項

### 1. 環境変数の確認
SSO関連の環境変数が正しく設定されているか確認：

```bash
docker compose exec web env | grep SSO
```

必要な環境変数：
- `SSO_HUB_BASE_URL` または `SSO_API_BASE_URL`
- `SSO_WEB_BASE_URL`
- `SSO_SYSTEM_KEY`
- `SSO_SERVICE_TOKEN`

### 2. ヘルスチェックエンドポイントの確認

```bash
# 直接アクセス
curl http://localhost:8000/api/health/

# nginx経由でアクセス（nginxサービスが動いている場合）
curl http://localhost/api/health/
```

### 3. SSOエンドポイントの確認

```bash
# SSOログインエンドポイント
curl -I http://localhost:8000/sso/login/

# SSOコールバックエンドポイント
curl -I http://localhost:8000/sso/callback/
```

## トラブルシューティング

### 問題1: webサービスが起動しない

```bash
# webサービスのログを詳細に確認
docker compose logs web

# webサービスを手動で起動してエラーを確認
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py migrate
```

### 問題2: nginxがwebサービスに接続できない

```bash
# Dockerネットワークを確認
docker network inspect backend_default

# webサービスがネットワークに接続されているか確認
docker compose exec web hostname
docker compose exec nginx ping web
```

### 問題3: SSO APIへの接続がタイムアウトする

```bash
# SSO APIのURLを確認
docker compose exec web env | grep SSO_API_BASE_URL

# SSO APIへの接続をテスト
docker compose exec web curl -v --max-time 30 <SSO_API_BASE_URL>/api/sso/ticket/verify
```

## 修正後の確認

1. **コンテナが正常に起動しているか確認**
   ```bash
   docker compose ps
   ```

2. **SSO処理が正常に動作するか確認**
   - ブラウザでSSOログインを試行
   - エラーログを確認

3. **ログを確認**
   ```bash
   docker compose logs web | tail -50
   ```

## 参考資料
- `TROUBLESHOOTING_NGINX.md` - nginx競合問題の解決手順
- `SOLVE_NGINX_VIA_VNC.md` - VNCコンソールからの解決手順
