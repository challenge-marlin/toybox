# webサービスをbackend_defaultネットワークに接続する最終手順

## 現在の状況

- Caddyコンテナは`backend_default`ネットワークに接続されている
- しかし、`web`サービスが`backend_default`ネットワークに接続されていない可能性がある
- そのため、Caddyが`web`というホスト名をDNS解決できない

## 解決手順

### ステップ1: webサービスの状態とネットワークを確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスのネットワークを確認
docker inspect $WEB_CONTAINER_ID | grep -A 30 "Networks"
```

### ステップ2: backend_defaultネットワークに接続されているコンテナを確認

```bash
# backend_defaultネットワークに接続されているすべてのコンテナを確認
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 2

# webサービスが接続されているか確認
docker network inspect backend_default | grep -E "web" -A 5
```

### ステップ3: webサービスをbackend_defaultネットワークに接続

webサービスが`backend_default`ネットワークに接続されていない場合：

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

### ステップ4: webサービスを再起動

```bash
cd /var/www/toybox/backend

# webサービスを再起動（ネットワーク設定を反映）
docker compose restart web

# webサービスが起動するまで待つ
sleep 10

# webサービスの状態を確認
docker compose ps | grep web
```

### ステップ5: DNS解決と接続を確認

```bash
cd /var/www/toybox

# DNS解決を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# webサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/
```

### ステップ6: Caddyのログを確認

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

# 2. webサービスのネットワークを確認
echo "=== Web service networks ==="
docker inspect $WEB_CONTAINER_ID | grep -A 30 "Networks"

# 3. backend_defaultネットワークに接続されているコンテナを確認
echo "=== Containers in backend_default network ==="
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 2

# 4. webサービスをbackend_defaultネットワークに接続
echo "=== Connecting web service to backend_default ==="
docker network connect backend_default $WEB_CONTAINER_ID

# 5. 接続を確認
echo "=== Verifying connection ==="
docker network inspect backend_default | grep -E "caddy|web" -A 5

# 6. webサービスを再起動
echo "=== Restarting web service ==="
docker compose restart web

# 7. webサービスが起動するまで待つ
echo "=== Waiting for web service to start ==="
sleep 10

# 8. webサービスの状態を確認
echo "=== Web service status ==="
docker compose ps | grep web

# 9. DNS解決を確認
echo "=== Testing DNS resolution ==="
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# 10. webサービスに接続テスト
echo "=== Testing connection to web service ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/
```

---

## トラブルシューティング

### 問題1: webサービスが起動していない

```bash
cd /var/www/toybox/backend

# webサービスを起動
docker compose up -d --build web

# webサービスのログを確認
docker compose logs web --tail=50
```

### 問題2: ネットワーク接続が失敗する

```bash
# ネットワークが存在するか確認
docker network ls | grep backend_default

# ネットワークが存在しない場合、backendディレクトリのコンテナを起動
cd /var/www/toybox/backend
docker compose up -d
cd ..
```

### 問題3: webサービスのコンテナIDが取得できない

```bash
cd /var/www/toybox/backend

# すべてのコンテナを確認
docker compose ps -a

# webサービスが存在するか確認
docker compose ps | grep web

# コンテナ名で直接指定（例: backend-web-1）
docker network connect backend_default backend-web-1
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ webサービスが`backend_default`ネットワークに接続されている
2. ✅ Caddyとwebサービスが同じネットワークに接続されている
3. ✅ DNS解決ができる（`nslookup web`でIPアドレスが返る）
4. ✅ Caddyからwebサービスに接続できる（`curl http://web:8000/api/health/`）
5. ✅ Caddyのログに"lookup web"エラーがない
