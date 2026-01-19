# webサービスをbackend_defaultネットワークに接続する手順

## 問題の確認

`backend_default`ネットワークにはCaddyコンテナ（`toybox-caddy-1`）しか接続されていません。
`web`サービスが接続されていないため、Caddyが`web`というホスト名をDNS解決できません。

## 解決手順

### ステップ1: webサービスのコンテナIDと名前を確認

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスのコンテナ名を確認
docker compose ps | grep web

# webサービスの詳細情報を確認
docker inspect $WEB_CONTAINER_ID | grep -A 30 "Networks"
```

### ステップ2: webサービスをbackend_defaultネットワークに接続

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスをbackend_defaultネットワークに接続
docker network connect backend_default $WEB_CONTAINER_ID

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

### ステップ3: webサービスを再起動

```bash
cd /var/www/toybox/backend

# webサービスを再起動（ネットワーク設定を反映）
docker compose restart web

# webサービスが起動するまで待つ
sleep 10

# webサービスの状態を確認
docker compose ps | grep web
```

### ステップ4: DNS解決と接続を確認

```bash
cd /var/www/toybox

# DNS解決を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# webサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/
```

### ステップ5: Caddyのログを確認

```bash
cd /var/www/toybox

# 最新のログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=20

# エラーが解消されたか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i "lookup web" | tail -3
```

---

## 一括実行コマンド

以下のコマンドを順番に実行してください：

```bash
# 1. webサービスのコンテナIDを取得
cd /var/www/toybox/backend
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# 2. webサービスのコンテナ名を確認
echo "=== Web service container name ==="
docker compose ps | grep web

# 3. webサービスをbackend_defaultネットワークに接続
echo "=== Connecting web service to backend_default ==="
docker network connect backend_default $WEB_CONTAINER_ID

# 4. 接続を確認
echo "=== Verifying connection ==="
docker network inspect backend_default | grep -E "caddy|web" -A 5

# 5. webサービスを再起動
echo "=== Restarting web service ==="
docker compose restart web

# 6. webサービスが起動するまで待つ
echo "=== Waiting for web service to start ==="
sleep 10

# 7. webサービスの状態を確認
echo "=== Web service status ==="
docker compose ps | grep web

# 8. DNS解決を確認
echo "=== Testing DNS resolution ==="
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# 9. webサービスに接続テスト
echo "=== Testing connection to web service ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/

# 10. Caddyのログを確認
echo "=== Checking Caddy logs ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=10
```

---

## トラブルシューティング

### 問題1: ネットワーク接続が失敗する

```bash
cd /var/www/toybox/backend

# ネットワークが存在するか確認
docker network ls | grep backend_default

# webサービスのコンテナIDを再確認
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# コンテナが存在するか確認
docker ps | grep $WEB_CONTAINER_ID

# ネットワーク接続を再試行
docker network connect backend_default $WEB_CONTAINER_ID
```

### 問題2: webサービスが起動していない

```bash
cd /var/www/toybox/backend

# webサービスを起動
docker compose up -d --build web

# webサービスのログを確認
docker compose logs web --tail=50
```

### 問題3: コンテナ名で直接指定する

コンテナIDが取得できない場合：

```bash
cd /var/www/toybox/backend

# webサービスのコンテナ名を確認
WEB_CONTAINER_NAME=$(docker compose ps --format json | jq -r '.[] | select(.Service=="web") | .Name')
echo "Web container name: $WEB_CONTAINER_NAME"

# コンテナ名でネットワークに接続
docker network connect backend_default $WEB_CONTAINER_NAME

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ webサービスが`backend_default`ネットワークに接続されている
2. ✅ Caddyとwebサービスが同じネットワークに接続されている
3. ✅ DNS解決ができる（`nslookup web`でIPアドレスが返る）
4. ✅ Caddyからwebサービスに接続できる（`curl http://web:8000/api/health/`）
5. ✅ Caddyのログに"lookup web"エラーがない
