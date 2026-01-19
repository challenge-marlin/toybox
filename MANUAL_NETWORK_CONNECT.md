# Caddyコンテナを手動でネットワークに接続する手順

## 問題の確認

ログから以下が確認できました：
- Caddyコンテナが`web`というホスト名をDNS解決できない（`SERVFAIL`）
- Caddyコンテナが`toybox_default`ネットワークに接続されている可能性がある
- webサービスが`backend_default`ネットワークに接続されている

## 解決手順

### ステップ1: CaddyコンテナのIDを正しく取得

```bash
# CaddyコンテナのIDを取得（複数の方法を試す）
CADDY_CONTAINER_ID=$(docker ps -q --filter "ancestor=caddy")
echo "Caddy container ID (ancestor): $CADDY_CONTAINER_ID"

# または、コンテナ名で取得
CADDY_CONTAINER_ID=$(docker ps -q --filter "name=caddy")
echo "Caddy container ID (name): $CADDY_CONTAINER_ID"

# または、直接確認
docker ps | grep caddy

# コンテナIDを手動でコピー（上記のコマンドで表示されたID）
# 例: CADDY_CONTAINER_ID="abc123def456"
```

### ステップ2: Caddyコンテナの現在のネットワークを確認

```bash
# CaddyコンテナのIDを設定（上記で取得したIDを使用）
CADDY_CONTAINER_ID=$(docker ps | grep caddy | awk '{print $1}')
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# 現在のネットワークを確認
docker inspect $CADDY_CONTAINER_ID | grep -A 30 "Networks"
```

### ステップ3: Caddyコンテナをbackend_defaultネットワークに接続

```bash
# CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps | grep caddy | awk '{print $1}')
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# 現在のネットワークから切断（toybox_defaultがある場合）
docker network disconnect toybox_default $CADDY_CONTAINER_ID 2>/dev/null || echo "toybox_default network not found or already disconnected"

# backend_defaultネットワークに接続
docker network connect backend_default $CADDY_CONTAINER_ID

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

### ステップ4: Caddyコンテナを再起動

```bash
# CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps | grep caddy | awk '{print $1}')
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# Caddyコンテナを再起動
docker restart $CADDY_CONTAINER_ID

# コンテナの状態を確認
docker ps | grep caddy
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
# 1. CaddyコンテナのIDを取得
CADDY_CONTAINER_ID=$(docker ps | grep caddy | awk '{print $1}')
echo "Caddy container ID: $CADDY_CONTAINER_ID"

# 2. 現在のネットワークを確認
echo "=== Current networks ==="
docker inspect $CADDY_CONTAINER_ID | grep -A 30 "Networks"

# 3. toybox_defaultネットワークから切断（エラーは無視）
echo "=== Disconnecting from toybox_default ==="
docker network disconnect toybox_default $CADDY_CONTAINER_ID 2>/dev/null || echo "Already disconnected or not connected"

# 4. backend_defaultネットワークに接続
echo "=== Connecting to backend_default ==="
docker network connect backend_default $CADDY_CONTAINER_ID

# 5. 接続を確認
echo "=== Verifying connection ==="
docker network inspect backend_default | grep -E "caddy|web" -A 5

# 6. Caddyコンテナを再起動
echo "=== Restarting Caddy ==="
docker restart $CADDY_CONTAINER_ID

# 7. 少し待つ（コンテナが起動するまで）
sleep 5

# 8. DNS解決を確認
echo "=== Testing DNS resolution ==="
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web

# 9. webサービスに接続テスト
echo "=== Testing connection to web service ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/
```

---

## トラブルシューティング

### 問題1: コンテナIDが取得できない

```bash
# すべてのコンテナを確認
docker ps -a | grep caddy

# コンテナ名で直接指定
docker network connect backend_default toybox-caddy-1
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

### 問題3: docker-compose.prod.ymlを修正して再作成

```bash
cd /var/www/toybox

# docker-compose.prod.ymlを修正（versionを削除）
cat > docker-compose.prod.yml << 'EOF'
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

## 確認事項

修正後、以下を確認してください：

1. ✅ Caddyコンテナが`backend_default`ネットワークに接続されている
2. ✅ webサービスが`backend_default`ネットワークに接続されている
3. ✅ DNS解決ができる（`nslookup web`でIPアドレスが返る）
4. ✅ Caddyからwebサービスに接続できる（`curl http://web:8000/api/health/`）
5. ✅ Caddyのログに"lookup web"エラーがない
