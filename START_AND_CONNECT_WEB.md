# サービスを起動してwebサービスをネットワークに接続する手順

## 前提条件
- Dockerイメージと.envファイルは`/var/www/toybox/backend`に存在する
- サービスを起動して、webサービスを`backend_default`ネットワークに接続する必要がある

## 解決手順

### ステップ1: サービスを起動

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
# 1. サービスを起動
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

# 5. webサービスが起動しているか確認
if [ -z "$WEB_CONTAINER_ID" ]; then
    echo "ERROR: Web service is not running"
    echo "Checking web service logs..."
    docker compose logs web --tail=50
    exit 1
fi

# 6. webサービスをbackend_defaultネットワークに接続
echo "=== Connecting web service to backend_default ==="
docker network connect backend_default $WEB_CONTAINER_ID

# 7. 接続を確認
echo "=== Verifying connection ==="
docker network inspect backend_default | grep -E "caddy|web" -A 5

# 8. webサービスを再起動
echo "=== Restarting web service ==="
docker compose restart web

# 9. webサービスが起動するまで待つ
sleep 10

# 10. DNS解決を確認
echo "=== Testing DNS resolution ==="
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# 11. webサービスに接続テスト
echo "=== Testing connection to web service ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/

# 12. Caddyのログを確認
echo "=== Checking Caddy logs ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=10
```

---

## トラブルシューティング

### 問題1: webサービスが起動しない

```bash
cd /var/www/toybox/backend

# webサービスのログを確認
docker compose logs web --tail=100

# webサービスを個別に起動
docker compose up -d --build web

# webサービスの状態を確認
docker compose ps | grep web
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

### 問題3: DNS解決ができない

```bash
cd /var/www/toybox

# Caddyコンテナ内からwebサービスのIPアドレスを直接確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy ping -c 1 web

# webサービスのIPアドレスを取得
cd /var/www/toybox/backend
WEB_IP=$(docker inspect $(docker compose ps -q web) | grep -A 10 "Networks" | grep "backend_default" -A 5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
echo "Web service IP: $WEB_IP"

# IPアドレスで直接接続テスト
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://${WEB_IP}:8000/api/health/
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
