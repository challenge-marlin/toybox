# 画像表示修正手順

## 問題
Caddyコンテナに`/app/public/uploads`ディレクトリがマウントされていないため、画像が404エラーで表示されない。

## 解決手順

### 1. docker-compose.prod.ymlを修正

サーバー上で以下を実行：

```bash
cd /var/www/toybox

# 現在のdocker-compose.prod.ymlを確認
cat docker-compose.prod.yml

# docker-compose.prod.ymlを修正（uploadsディレクトリをマウント）
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
      - ./backend/public/uploads:/app/public/uploads:ro
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

### 2. Caddyコンテナを再起動

```bash
cd /var/www/toybox

# Caddyコンテナを停止・削除
docker compose -f docker-compose.prod.yml stop caddy
docker compose -f docker-compose.prod.yml rm -f caddy

# Caddyコンテナを再起動
docker compose -f docker-compose.prod.yml up -d

# 確認：Caddyコンテナが起動していることを確認
docker compose -f docker-compose.prod.yml ps
```

### 3. マウント確認

```bash
# Caddyコンテナ内で/uploadsディレクトリが存在するか確認
docker compose -f docker-compose.prod.yml exec caddy ls -la /app/public/uploads

# または、コンテナ内に入って確認
docker compose -f docker-compose.prod.yml exec caddy sh
# コンテナ内で: ls -la /app/public/uploads
# コンテナ内で: exit
```

### 4. 動作確認

```bash
# Caddyのログを確認
docker compose -f docker-compose.prod.yml logs caddy

# 画像URLにアクセスして確認（例）
curl -I http://localhost/uploads/submissions/10_1766547801.png
```

### 5. ブラウザで確認

- `https://toybox.ayatori-inc.co.jp` にアクセス
- 画像が表示されることを確認

## トラブルシューティング

### マウントが失敗する場合

```bash
# ホスト側のディレクトリが存在するか確認
ls -la /var/www/toybox/backend/public/uploads

# パーミッションを確認
ls -ld /var/www/toybox/backend/public/uploads

# 必要に応じてパーミッションを修正
chmod -R 755 /var/www/toybox/backend/public/uploads
```

### まだ404エラーが出る場合

```bash
# Caddyfileの設定を確認
cat /var/www/toybox/Caddyfile | grep -A 3 "handle /uploads"

# Caddyのログでエラーを確認
docker compose -f docker-compose.prod.yml logs caddy | tail -50
```
