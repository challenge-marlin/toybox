# ネットワーク接続の修正手順

## 問題の原因

Dockerネットワークが2つ存在しています：
- `backend_default` - webサービスが接続されている
- `toybox_default` - Caddyコンテナが接続されている可能性

Caddyとwebサービスが異なるネットワークに接続されているため、Caddyが`web`というホスト名をDNS解決できません。

## 解決手順

### ステップ1: 現在の接続状況を確認

```bash
# webサービスがどのネットワークに接続されているか確認
docker network inspect backend_default | grep -E "web" -A 5

# Caddyコンテナがどのネットワークに接続されているか確認
docker network inspect toybox_default | grep -E "caddy" -A 5

# または、Caddyコンテナのネットワークを直接確認
docker inspect $(docker ps -q --filter "ancestor=caddy") | grep -A 20 "Networks"
```

### ステップ2: docker-compose.prod.ymlを修正

Caddyコンテナを`backend_default`ネットワークに接続するように修正：

```bash
cd /var/www/toybox

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

# 修正内容を確認
cat docker-compose.prod.yml
```

### ステップ3: Caddyコンテナを再作成

```bash
cd /var/www/toybox

# Caddyコンテナを停止
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop caddy

# Caddyコンテナを削除
docker compose -f docker-compose.yml -f docker-compose.prod.yml rm -f caddy

# Caddyコンテナを再作成（backend_defaultネットワークに接続）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build caddy

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### ステップ4: ネットワーク接続を確認

```bash
# Caddyとwebサービスが同じネットワーク（backend_default）に接続されているか確認
docker network inspect backend_default | grep -E "caddy|web" -A 5

# Caddyコンテナ内からwebサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/

# DNS解決を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web
```

### ステップ5: Caddyのログを確認

```bash
cd /var/www/toybox

# Caddyのログを確認（最新20行）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=20

# エラーが解消されたか確認（"lookup web"エラーが表示されないはず）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i "lookup web" | tail -5
```

### ステップ6: 動作確認

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# ヘルスチェックエンドポイントをテスト
curl http://toybox.ayatori-inc.co.jp/health
```

---

## トラブルシューティング

### 問題1: Caddyコンテナがまだtoybox_defaultネットワークに接続されている

```bash
# Caddyコンテナを手動でbackend_defaultネットワークに接続
docker network connect backend_default $(docker ps -q --filter "ancestor=caddy")

# toybox_defaultネットワークから切断（オプション）
docker network disconnect toybox_default $(docker ps -q --filter "ancestor=caddy")

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web"
```

### 問題2: webサービスがbackend_defaultネットワークに接続されていない

```bash
cd /var/www/toybox/backend

# webサービスを再起動
docker compose restart web

# ネットワーク接続を確認
docker network inspect backend_default | grep -A 5 "web"
```

### 問題3: docker-compose.prod.ymlを修正しても反映されない

```bash
cd /var/www/toybox

# すべてのコンテナを停止
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# コンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# ネットワーク接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ Caddyとwebサービスが同じネットワーク（`backend_default`）に接続されている
2. ✅ Caddyからwebサービスに接続できる（`docker exec caddy curl http://web:8000/api/health/`）
3. ✅ DNS解決ができる（`docker exec caddy nslookup web`）
4. ✅ Caddyのログに"lookup web"エラーがない
5. ✅ ブラウザで`https://toybox.ayatori-inc.co.jp`にアクセスできる
