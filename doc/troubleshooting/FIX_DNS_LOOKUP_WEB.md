# DNS lookup web エラー解決手順

## 問題の原因

Caddyのログに以下のエラーが繰り返し表示されています：
```
"dial tcp: lookup web on 127.0.0.11:53: server misbehaving"
```

**原因**: Caddyコンテナとwebサービスが異なるDockerネットワークに接続されているため、Caddyが`web`というホスト名をDNS解決できません。

## 解決手順

### ステップ1: Dockerネットワークを確認

```bash
# Dockerネットワーク一覧を確認
docker network ls

# backendディレクトリのネットワーク名を確認
cd /var/www/toybox/backend
docker compose config | grep -A 5 "networks:"

# 実際のネットワーク名を確認（通常は "backend_default" または "toybox_backend_default"）
docker compose ps
docker network inspect $(docker compose ps -q web | head -1) 2>/dev/null | grep -A 5 "Networks"
```

### ステップ2: webサービスが起動しているか確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps | grep web

# webサービスが起動していない場合、起動
docker compose up -d --build

# webサービスがネットワークに接続されているか確認
docker network inspect backend_default | grep -A 5 "web"
```

### ステップ3: docker-compose.prod.ymlのネットワーク設定を確認・修正

```bash
cd /var/www/toybox

# docker-compose.prod.ymlの内容を確認
cat docker-compose.prod.yml

# ネットワーク名が正しいか確認
# backendディレクトリの実際のネットワーク名を確認
cd backend
NETWORK_NAME=$(docker compose config 2>/dev/null | grep -A 5 "networks:" | grep -v "^#" | head -1 | awk '{print $1}' | tr -d ':')
echo "Network name: $NETWORK_NAME"

# または、直接確認
docker compose config | grep -A 10 "networks:" | head -10
cd ..
```

### ステップ4: docker-compose.prod.ymlを修正

実際のネットワーク名に合わせて`docker-compose.prod.yml`を修正してください：

```bash
cd /var/www/toybox

# バックアップを作成
cp docker-compose.prod.yml docker-compose.prod.yml.backup

# docker-compose.prod.ymlを修正
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
```

**注意**: ネットワーク名が`backend_default`でない場合（例: `toybox_backend_default`）、上記の`backend_default`を実際のネットワーク名に置き換えてください。

### ステップ5: Caddyコンテナを再作成

```bash
cd /var/www/toybox

# Caddyコンテナを停止
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop caddy

# Caddyコンテナを削除
docker compose -f docker-compose.yml -f docker-compose.prod.yml rm -f caddy

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build caddy

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### ステップ6: ネットワーク接続を確認

```bash
# Caddyとwebサービスが同じネットワークに接続されているか確認
docker network inspect backend_default | grep -E "caddy|web" -A 5

# Caddyコンテナ内からwebサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/

# DNS解決を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web
```

### ステップ7: Caddyのログを確認

```bash
cd /var/www/toybox

# Caddyのログを確認（最新20行）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=20

# エラーが解消されたか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i "lookup web" | tail -5
```

### ステップ8: 動作確認

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# ヘルスチェックエンドポイントをテスト
curl http://toybox.ayatori-inc.co.jp/health
```

---

## ネットワーク名が異なる場合の対処法

### 方法A: ネットワーク名を確認して修正

```bash
cd /var/www/toybox/backend

# 実際のネットワーク名を確認
docker compose config | grep -A 10 "networks:" | head -15

# または、webサービスのネットワークを確認
docker inspect $(docker compose ps -q web) | grep -A 20 "Networks" | grep -E "NetworkID|backend"
```

ネットワーク名が`toybox_backend_default`の場合：

```bash
cd /var/www/toybox

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
      - toybox_backend_default

networks:
  toybox_backend_default:
    external: true

volumes:
  caddy-data:
  caddy-config:
EOF
```

### 方法B: ネットワーク名を自動取得して修正

```bash
cd /var/www/toybox/backend

# webサービスが接続されているネットワーク名を取得
NETWORK_NAME=$(docker inspect $(docker compose ps -q web) | grep -A 20 "Networks" | grep -oP '"([^"]+backend[^"]+)"' | head -1 | tr -d '"')
echo "Network name: $NETWORK_NAME"

cd /var/www/toybox

# docker-compose.prod.ymlを動的に生成
cat > docker-compose.prod.yml << EOF
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
      - ${NETWORK_NAME}

networks:
  ${NETWORK_NAME}:
    external: true

volumes:
  caddy-data:
  caddy-config:
EOF

cat docker-compose.prod.yml
```

---

## トラブルシューティング

### 問題1: ネットワークが存在しない

```bash
# backendディレクトリのコンテナを起動してネットワークを作成
cd /var/www/toybox/backend
docker compose up -d

# ネットワークが作成されたか確認
docker network ls | grep backend
```

### 問題2: Caddyコンテナがネットワークに接続されない

```bash
# Caddyコンテナを手動でネットワークに接続
cd /var/www/toybox

# ネットワーク名を確認
NETWORK_NAME=$(docker network ls | grep backend | awk '{print $2}' | head -1)
echo "Network name: $NETWORK_NAME"

# Caddyコンテナをネットワークに接続
docker network connect ${NETWORK_NAME} $(docker ps -q --filter "ancestor=caddy")

# 接続を確認
docker network inspect ${NETWORK_NAME} | grep -E "caddy|web"
```

### 問題3: webサービスがネットワークに接続されていない

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

1. ✅ webサービスが起動している（`cd /var/www/toybox/backend && docker compose ps | grep web`）
2. ✅ Caddyとwebサービスが同じネットワークに接続されている（`docker network inspect backend_default | grep -E "caddy|web"`）
3. ✅ Caddyからwebサービスに接続できる（`docker exec caddy curl http://web:8000/api/health/`）
4. ✅ DNS解決ができる（`docker exec caddy nslookup web`）
5. ✅ Caddyのログにエラーがない（`docker logs caddy | grep -i "lookup web"`）
