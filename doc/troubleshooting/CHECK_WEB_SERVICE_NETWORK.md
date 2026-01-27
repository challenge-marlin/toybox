# webサービスのネットワーク接続確認手順

## 問題の確認

Caddyコンテナは`backend_default`ネットワークに接続されていますが、`web`サービスが同じネットワークに接続されていない可能性があります。

## 確認手順

### ステップ1: webサービスがどのネットワークに接続されているか確認

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

### ステップ2: backend_defaultネットワークに接続されているすべてのコンテナを確認

```bash
# backend_defaultネットワークに接続されているすべてのコンテナを確認
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 2

# webサービスが接続されているか確認
docker network inspect backend_default | grep -E "web" -A 5
```

### ステップ3: webサービスが起動しているか確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps | grep web

# webサービスのログを確認
docker compose logs web --tail=20
```

### ステップ4: webサービスをbackend_defaultネットワークに接続（必要に応じて）

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

### ステップ5: webサービスの実際のサービス名を確認

`backend/docker-compose.yml`でサービス名が`web`でない可能性があります：

```bash
cd /var/www/toybox/backend

# docker-compose.ymlのサービス名を確認
cat docker-compose.yml | grep -A 5 "services:"
cat docker-compose.yml | grep -A 10 "web:"

# 実際のサービス名を確認
docker compose config | grep -A 5 "services:" | head -10
```

### ステップ6: Caddyfileのサービス名を確認

Caddyfileで`web:8000`を参照していますが、実際のサービス名が異なる可能性があります：

```bash
cd /var/www/toybox

# Caddyfileの内容を確認
cat Caddyfile | grep -E "reverse_proxy|web:"
```

---

## 解決手順

### 方法A: webサービスをbackend_defaultネットワークに接続

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスをbackend_defaultネットワークに接続
docker network connect backend_default $WEB_CONTAINER_ID

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5

# webサービスを再起動（ネットワーク設定を反映）
docker compose restart web
```

### 方法B: backend/docker-compose.ymlでネットワークを明示的に指定

`backend/docker-compose.yml`で`backend_default`ネットワークを明示的に指定：

```bash
cd /var/www/toybox/backend

# docker-compose.ymlのバックアップを作成
cp docker-compose.yml docker-compose.yml.backup

# docker-compose.ymlを確認
cat docker-compose.yml | tail -10
```

`backend/docker-compose.yml`の最後に以下を追加：

```yaml
networks:
  default:
    name: backend_default
    external: true
```

### 方法C: CaddyfileでIPアドレスを直接指定（一時的な解決策）

webサービスのIPアドレスを直接指定：

```bash
cd /var/www/toybox/backend

# webサービスのIPアドレスを取得
WEB_IP=$(docker inspect $(docker compose ps -q web) | grep -A 10 "Networks" | grep "backend_default" -A 5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
echo "Web service IP: $WEB_IP"

cd /var/www/toybox

# Caddyfileをバックアップ
cp Caddyfile Caddyfile.backup

# Caddyfileを修正（IPアドレスを直接指定）
sed -i "s/web:8000/${WEB_IP}:8000/g" Caddyfile

# 修正内容を確認
cat Caddyfile | grep -E "reverse_proxy|8000"

# Caddyコンテナを再起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart caddy
```

---

## 一括確認コマンド

以下のコマンドを順番に実行して、状況を確認してください：

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

# 4. webサービスがbackend_defaultネットワークに接続されているか確認
echo "=== Checking if web is in backend_default ==="
docker network inspect backend_default | grep -E "web" -A 5

# 5. webサービスが起動しているか確認
echo "=== Web service status ==="
docker compose ps | grep web
```

---

## トラブルシューティング

### 問題1: webサービスがbackend_defaultネットワークに接続されていない

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)

# webサービスをbackend_defaultネットワークに接続
docker network connect backend_default $WEB_CONTAINER_ID

# webサービスを再起動
docker compose restart web

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

### 問題2: webサービスが起動していない

```bash
cd /var/www/toybox/backend

# webサービスを起動
docker compose up -d --build web

# webサービスのログを確認
docker compose logs web --tail=50
```

### 問題3: サービス名が`web`でない

`backend/docker-compose.yml`でサービス名を確認し、Caddyfileを修正する必要があります。

---

## 確認事項

修正後、以下を確認してください：

1. ✅ webサービスが`backend_default`ネットワークに接続されている
2. ✅ Caddyとwebサービスが同じネットワークに接続されている
3. ✅ DNS解決ができる（`docker exec caddy nslookup web`）
4. ✅ Caddyからwebサービスに接続できる（`docker exec caddy curl http://web:8000/api/health/`）
