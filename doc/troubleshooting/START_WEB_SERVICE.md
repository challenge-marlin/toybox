# webサービスを起動してネットワークに接続する手順

## 問題
backendディレクトリのすべてのサービスが停止しています。webサービスを起動する必要があります。

## 解決手順

### ステップ1: すべてのサービスを起動

webサービスは`db`と`redis`に依存しているため、すべてのサービスを起動します：

```bash
cd /var/www/toybox/backend

# すべてのサービスを起動
docker compose up -d

# サービスが起動するまで待つ
sleep 15

# サービス状態を確認
docker compose ps
```

### ステップ2: webサービスのコンテナIDを取得

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスのコンテナ名を確認
docker compose ps | grep web
```

### ステップ3: webサービスをbackend_defaultネットワークに接続

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
# 1. すべてのサービスを起動
cd /var/www/toybox/backend
echo "=== Starting all services ==="
docker compose up -d

# 2. サービスが起動するまで待つ
echo "=== Waiting for services to start ==="
sleep 15

# 3. サービス状態を確認
echo "=== Service status ==="
docker compose ps

# 4. webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# 5. webサービスをbackend_defaultネットワークに接続
echo "=== Connecting web service to backend_default ==="
docker network connect backend_default $WEB_CONTAINER_ID

# 6. 接続を確認
echo "=== Verifying connection ==="
docker network inspect backend_default | grep -E "caddy|web" -A 5

# 7. webサービスを再起動
echo "=== Restarting web service ==="
docker compose restart web

# 8. webサービスが起動するまで待つ
sleep 10

# 9. DNS解決を確認
echo "=== Testing DNS resolution ==="
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# 10. webサービスに接続テスト
echo "=== Testing connection to web service ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/

# 11. Caddyのログを確認
echo "=== Checking Caddy logs ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=10
```

---

## トラブルシューティング

### 問題1: サービスが起動しない

```bash
cd /var/www/toybox/backend

# サービスのログを確認
docker compose logs --tail=50

# webサービスのログを確認
docker compose logs web --tail=50

# dbサービスのログを確認
docker compose logs db --tail=50
```

### 問題2: ネットワーク接続が失敗する

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

### 問題3: webサービスが起動しない

```bash
cd /var/www/toybox/backend

# webサービスを個別に起動
docker compose up -d --build web

# webサービスのログを確認
docker compose logs web --tail=100
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ すべてのサービスが起動している（`docker compose ps`）
2. ✅ webサービスが`backend_default`ネットワークに接続されている
3. ✅ Caddyとwebサービスが同じネットワークに接続されている
4. ✅ DNS解決ができる（`nslookup web`でIPアドレスが返る）
5. ✅ Caddyからwebサービスに接続できる（`curl http://web:8000/api/health/`）
6. ✅ Caddyのログに"lookup web"エラーがない
