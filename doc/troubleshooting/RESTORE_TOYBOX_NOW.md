# TOYBOX緊急復旧手順

## 問題
- `backend/docker-compose.yml`の`nginx`が80/443ポートを使用
- `backend/docker-compose.yml`の`web`が8000ポートを使用
- `/var/www/toybox`でCaddyを起動しようとしているがポート競合

## 解決手順（順番に実行）

### 1. 現在の状況を確認

```bash
# ポート80/443/8000を使用しているコンテナを確認
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "80|443|8000"

# backendディレクトリのコンテナ状態
cd /var/www/toybox/backend
docker compose ps
```

### 2. backendのnginxを停止・削除（重要）

```bash
cd /var/www/toybox/backend

# nginxサービスを停止
docker compose stop nginx

# nginxコンテナを削除（ポートを解放）
docker compose rm -f nginx

# 確認：nginxが停止していることを確認
docker ps | grep nginx
# （何も表示されなければOK）
```

### 3. backendのwebサービスを起動（Caddyが接続するため必要）

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps | grep web

# 起動していない場合は起動
docker compose up -d web db redis worker beat

# 確認：webサービスが起動していることを確認
docker compose ps
# webサービスが "Up" になっていることを確認
```

### 4. backend_defaultネットワークを確認

```bash
# backend_defaultネットワークが存在するか確認
docker network ls | grep backend

# 存在しない場合は、backendディレクトリで一度起動して作成
cd /var/www/toybox/backend
docker compose up -d
docker network ls | grep backend
```

### 5. /var/www/toyboxでdocker-compose.prod.ymlを確認・作成

```bash
cd /var/www/toybox

# docker-compose.prod.ymlが存在するか確認
ls -la docker-compose.prod.yml

# 存在しない場合、作成
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

### 6. Caddyを起動

```bash
cd /var/www/toybox

# 既存のCaddyコンテナがあれば停止・削除
docker compose -f docker-compose.prod.yml stop caddy 2>/dev/null
docker compose -f docker-compose.prod.yml rm -f caddy 2>/dev/null

# Caddyを起動
docker compose -f docker-compose.prod.yml up -d

# 確認：Caddyが起動していることを確認
docker compose -f docker-compose.prod.yml ps
docker ps | grep caddy
```

### 7. 動作確認

```bash
# Caddyのログを確認
docker compose -f docker-compose.prod.yml logs caddy

# ポート80/443が使用されているか確認
netstat -tlnp | grep -E ':80|:443'

# webサービスにアクセスできるか確認
curl -I http://localhost/health
```

### 8. ブラウザで確認

- `https://toybox.ayatori-inc.co.jp` にアクセス
- サイトが表示されることを確認

## トラブルシューティング

### ポートがまだ使用されている場合

```bash
# ポート80/443を使用しているプロセスを確認
sudo netstat -tlnp | grep -E ':80|:443'

# Dockerコンテナ以外が使用している場合は停止
# （例：systemdのnginx）
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### Caddyがwebサービスに接続できない場合

```bash
# backend_defaultネットワークにCaddyが接続されているか確認
docker network inspect backend_default | grep -A 10 "caddy"

# 接続されていない場合、手動で接続
docker network connect backend_default $(docker ps -q --filter "ancestor=caddy:2")
```

### webサービスが起動しない場合

```bash
cd /var/www/toybox/backend

# webサービスのログを確認
docker compose logs web

# webサービスを再起動
docker compose restart web
```
