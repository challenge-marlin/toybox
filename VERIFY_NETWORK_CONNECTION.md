# ネットワーク接続の確認と修正手順

## 現在の状況

Caddyのログにまだ以下のエラーが表示されています：
```
"dial tcp: lookup web on 127.0.0.11:53: server misbehaving"
```

これは、Caddyコンテナがまだ`backend_default`ネットワークに接続されていない可能性があります。

## 確認手順

### ステップ1: Caddyコンテナがどのネットワークに接続されているか確認

```bash
# CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps -q --filter "ancestor=caddy")
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# Caddyコンテナのネットワークを確認
docker inspect $CADDY_CONTAINER_ID | grep -A 30 "Networks"

# または、より詳細に確認
docker inspect $CADDY_CONTAINER_ID | jq '.[0].NetworkSettings.Networks'
```

### ステップ2: webサービスがどのネットワークに接続されているか確認

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスのネットワークを確認
docker inspect $WEB_CONTAINER_ID | grep -A 30 "Networks"

# または、より詳細に確認
docker inspect $WEB_CONTAINER_ID | jq '.[0].NetworkSettings.Networks'
```

### ステップ3: backend_defaultネットワークに接続されているコンテナを確認

```bash
# backend_defaultネットワークに接続されているすべてのコンテナを確認
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 2

# Caddyとwebサービスが接続されているか確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

### ステップ4: Caddyコンテナを手動でbackend_defaultネットワークに接続

Caddyコンテナが`backend_default`ネットワークに接続されていない場合：

```bash
# CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps -q --filter "ancestor=caddy")
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# Caddyコンテナをbackend_defaultネットワークに接続
docker network connect backend_default $CADDY_CONTAINER_ID

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

### ステップ5: Caddyコンテナ内からwebサービスに接続テスト

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
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=10

# エラーが解消されたか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i "lookup web" | tail -3
```

---

## 解決手順（ネットワーク接続が確認できない場合）

### 方法A: Caddyコンテナを完全に再作成

```bash
cd /var/www/toybox

# すべてのコンテナを停止
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# docker-compose.prod.ymlの内容を確認
cat docker-compose.prod.yml

# コンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# ネットワーク接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

### 方法B: Caddyコンテナを手動でネットワークに接続

```bash
# CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps -q --filter "ancestor=caddy")
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# 現在のネットワークを確認
docker inspect $CADDY_CONTAINER_ID | grep -A 30 "Networks"

# toybox_defaultネットワークから切断（接続されている場合）
docker network disconnect toybox_default $CADDY_CONTAINER_ID 2>/dev/null || true

# backend_defaultネットワークに接続
docker network connect backend_default $CADDY_CONTAINER_ID

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5

# Caddyコンテナを再起動（ネットワーク設定を反映）
docker restart $CADDY_CONTAINER_ID
```

### 方法C: docker-compose.prod.ymlを確認して修正

```bash
cd /var/www/toybox

# docker-compose.prod.ymlの内容を確認
cat docker-compose.prod.yml

# 正しい内容になっているか確認（backend_defaultが指定されているか）
grep -A 5 "networks:" docker-compose.prod.yml

# 修正が必要な場合、再作成
cat > docker-compose.prod.yml << 'EOF'
version: "3.8"

services:
  caddy:
    image: caddy:2
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    networks:
      - backend_default

networks:
  backend_default:
    external: true

volumes:
  caddy-data:
  caddy-config:
EOF

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

---

## 確認コマンド（一括実行）

以下のコマンドを順番に実行して、状況を確認してください：

```bash
# 1. Caddyコンテナのネットワークを確認
echo "=== Caddy container networks ==="
docker inspect $(docker ps -q --filter "ancestor=caddy") | grep -A 30 "Networks"

# 2. webサービスのネットワークを確認
echo "=== Web service networks ==="
cd /var/www/toybox/backend
docker inspect $(docker compose ps -q web) | grep -A 30 "Networks"
cd ..

# 3. backend_defaultネットワークに接続されているコンテナを確認
echo "=== Containers in backend_default network ==="
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 2

# 4. Caddyからwebサービスに接続テスト
echo "=== Testing connection from Caddy to web ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/
```

---

## トラブルシューティング

### 問題1: Caddyコンテナがtoybox_defaultネットワークに接続されている

```bash
# CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps -q --filter "ancestor=caddy")

# toybox_defaultネットワークから切断
docker network disconnect toybox_default $CADDY_CONTAINER_ID

# backend_defaultネットワークに接続
docker network connect backend_default $CADDY_CONTAINER_ID

# Caddyコンテナを再起動
docker restart $CADDY_CONTAINER_ID
```

### 問題2: docker-compose.prod.ymlが反映されない

```bash
cd /var/www/toybox

# docker-compose.prod.ymlの内容を確認
cat docker-compose.prod.yml

# すべてのコンテナを停止して再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 問題3: webサービスがbackend_defaultネットワークに接続されていない

```bash
cd /var/www/toybox/backend

# webサービスを再起動
docker compose restart web

# ネットワーク接続を確認
docker network inspect backend_default | grep -A 5 "web"
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ Caddyコンテナが`backend_default`ネットワークに接続されている
2. ✅ webサービスが`backend_default`ネットワークに接続されている
3. ✅ Caddyからwebサービスに接続できる（`docker exec caddy curl http://web:8000/api/health/`）
4. ✅ DNS解決ができる（`docker exec caddy nslookup web`）
5. ✅ Caddyのログに"lookup web"エラーがない
