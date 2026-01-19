# webサービスネットワーク問題の詳細診断

## 問題
`docker compose restart web`を実行しても何も変わらない。

## 詳細診断手順

### ステップ1: webサービスの詳細な状態を確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# webサービスの詳細情報を確認
docker inspect $WEB_CONTAINER_ID | grep -A 50 "NetworkSettings"

# webサービスがどのネットワークに接続されているか確認
docker inspect $WEB_CONTAINER_ID | jq '.[0].NetworkSettings.Networks'
```

### ステップ2: backend_defaultネットワークの詳細を確認

```bash
# backend_defaultネットワークの詳細を確認
docker network inspect backend_default

# すべてのコンテナ名とIPアドレスを確認
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 1

# webサービスが接続されているか確認（コンテナ名で検索）
docker network inspect backend_default | grep -i "web" -A 5
```

### ステップ3: webサービスの実際のコンテナ名を確認

Docker Composeは通常、`プロジェクト名-サービス名-番号`という形式でコンテナ名を付けます。

```bash
cd /var/www/toybox/backend

# webサービスの実際のコンテナ名を確認
docker compose ps --format json | jq -r '.[] | select(.Service=="web") | .Name'

# または、直接確認
docker compose ps | grep web
```

### ステップ4: Caddyfileで参照しているサービス名を確認

Caddyfileで`web:8000`を参照していますが、実際のサービス名やコンテナ名が異なる可能性があります。

```bash
cd /var/www/toybox

# Caddyfileの内容を確認
cat Caddyfile | grep -E "reverse_proxy|web:"
```

### ステップ5: webサービスのIPアドレスを直接確認

```bash
cd /var/www/toybox/backend

# webサービスのIPアドレスを取得
WEB_IP=$(docker inspect $(docker compose ps -q web) | grep -A 10 "Networks" | grep "backend_default" -A 5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
echo "Web service IP: $WEB_IP"

# IPアドレスが取得できたか確認
if [ -z "$WEB_IP" ]; then
    echo "Web service is not in backend_default network"
    # 別のネットワークを確認
    docker inspect $(docker compose ps -q web) | grep -A 10 "Networks"
else
    echo "Web service IP: $WEB_IP"
fi
```

### ステップ6: CaddyからIPアドレスで直接接続テスト

```bash
cd /var/www/toybox/backend

# webサービスのIPアドレスを取得
WEB_IP=$(docker inspect $(docker compose ps -q web) | grep -A 10 "Networks" | grep -E "backend_default|IPv4Address" | head -5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
echo "Web service IP: $WEB_IP"

cd /var/www/toybox

# IPアドレスで直接接続テスト
if [ ! -z "$WEB_IP" ]; then
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://${WEB_IP}:8000/api/health/
fi
```

---

## 解決手順

### 方法A: webサービスのコンテナ名を確認してCaddyfileを修正

webサービスの実際のコンテナ名が`web`でない場合、Caddyfileでコンテナ名を直接指定する必要があります。

```bash
cd /var/www/toybox/backend

# webサービスの実際のコンテナ名を確認
WEB_CONTAINER_NAME=$(docker compose ps --format json | jq -r '.[] | select(.Service=="web") | .Name')
echo "Web container name: $WEB_CONTAINER_NAME"

cd /var/www/toybox

# Caddyfileをバックアップ
cp Caddyfile Caddyfile.backup

# Caddyfileでコンテナ名を確認
cat Caddyfile | grep "reverse_proxy"
```

### 方法B: webサービスのIPアドレスを直接Caddyfileに指定（一時的な解決策）

```bash
cd /var/www/toybox/backend

# webサービスのIPアドレスを取得
WEB_IP=$(docker inspect $(docker compose ps -q web) | grep -A 10 "Networks" | grep "backend_default" -A 5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')

# IPアドレスが取得できない場合、別の方法で取得
if [ -z "$WEB_IP" ]; then
    # すべてのネットワークからIPアドレスを取得
    WEB_IP=$(docker inspect $(docker compose ps -q web) | grep "IPv4Address" | head -1 | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
fi

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

### 方法C: backend/docker-compose.ymlでネットワークを明示的に指定

`backend/docker-compose.yml`で`backend_default`ネットワークを明示的に指定：

```bash
cd /var/www/toybox/backend

# docker-compose.ymlのバックアップを作成
cp docker-compose.yml docker-compose.yml.backup

# docker-compose.ymlの最後を確認
cat docker-compose.yml | tail -10
```

`backend/docker-compose.yml`の最後に以下を追加：

```yaml
networks:
  default:
    name: backend_default
    external: true
```

その後、webサービスを再起動：

```bash
cd /var/www/toybox/backend

# webサービスを再作成
docker compose up -d --force-recreate web

# ネットワーク接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5
```

---

## 一括診断コマンド

以下のコマンドを順番に実行して、詳細な情報を収集してください：

```bash
# 1. webサービスの状態を確認
cd /var/www/toybox/backend
echo "=== Web service status ==="
docker compose ps

# 2. webサービスのコンテナIDと名前を確認
WEB_CONTAINER_ID=$(docker compose ps -q web)
WEB_CONTAINER_NAME=$(docker compose ps --format json | jq -r '.[] | select(.Service=="web") | .Name')
echo "Web container ID: $WEB_CONTAINER_ID"
echo "Web container name: $WEB_CONTAINER_NAME"

# 3. webサービスのネットワークを確認
echo "=== Web service networks ==="
docker inspect $WEB_CONTAINER_ID | grep -A 50 "NetworkSettings"

# 4. backend_defaultネットワークの詳細を確認
echo "=== backend_default network details ==="
docker network inspect backend_default | grep -E "Name|IPv4Address" -A 2

# 5. webサービスがbackend_defaultネットワークに接続されているか確認
echo "=== Checking if web is in backend_default ==="
docker network inspect backend_default | grep -i "$WEB_CONTAINER_NAME\|web" -A 5

# 6. webサービスのIPアドレスを取得
echo "=== Getting web service IP ==="
WEB_IP=$(docker inspect $WEB_CONTAINER_ID | grep -A 10 "Networks" | grep "backend_default" -A 5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
if [ -z "$WEB_IP" ]; then
    echo "Web service is NOT in backend_default network"
    echo "Trying to get IP from any network:"
    docker inspect $WEB_CONTAINER_ID | grep "IPv4Address" | head -1
else
    echo "Web service IP in backend_default: $WEB_IP"
fi

# 7. Caddyfileの内容を確認
cd /var/www/toybox
echo "=== Caddyfile content ==="
cat Caddyfile | grep -E "reverse_proxy|web:"
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

# 接続を確認
docker network inspect backend_default | grep -E "caddy|web" -A 5

# webサービスを再起動
docker compose restart web
```

### 問題2: webサービスが別のネットワークに接続されている

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)

# 現在のネットワークを確認
docker inspect $WEB_CONTAINER_ID | grep -A 30 "Networks"

# 現在のネットワークから切断（必要に応じて）
# docker network disconnect <network_name> $WEB_CONTAINER_ID

# backend_defaultネットワークに接続
docker network connect backend_default $WEB_CONTAINER_ID
```

### 問題3: webサービスのIPアドレスを直接使用する

DNS解決ができない場合、一時的にIPアドレスを直接使用：

```bash
cd /var/www/toybox/backend

# webサービスのIPアドレスを取得
WEB_IP=$(docker inspect $(docker compose ps -q web) | grep -A 10 "Networks" | grep "backend_default" -A 5 | grep "IPv4Address" | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')

# IPアドレスが取得できない場合、すべてのネットワークから取得
if [ -z "$WEB_IP" ]; then
    WEB_IP=$(docker inspect $(docker compose ps -q web) | grep "IPv4Address" | head -1 | awk -F'"' '{print $4}' | awk -F'/' '{print $1}')
fi

echo "Web service IP: $WEB_IP"

cd /var/www/toybox

# Caddyfileを修正
cp Caddyfile Caddyfile.backup
sed -i "s/web:8000/${WEB_IP}:8000/g" Caddyfile

# Caddyコンテナを再起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart caddy
```

---

## 確認事項

診断後、以下を確認してください：

1. ✅ webサービスが起動している
2. ✅ webサービスがどのネットワークに接続されているか
3. ✅ webサービスの実際のコンテナ名
4. ✅ webサービスのIPアドレス
5. ✅ Caddyfileで参照しているサービス名が正しいか
