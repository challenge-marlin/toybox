# webサービスを探す手順

## 問題
`docker compose ps | grep web`で何も出力されない = webサービスが起動していないか、サービス名が異なる可能性があります。

## 確認手順

### ステップ1: すべてのサービスを確認

```bash
cd /var/www/toybox/backend

# すべてのサービスを確認
docker compose ps

# すべてのサービス（停止中も含む）を確認
docker compose ps -a
```

### ステップ2: docker-compose.ymlのサービス名を確認

```bash
cd /var/www/toybox/backend

# docker-compose.ymlのサービス名を確認
cat docker-compose.yml | grep -A 5 "services:"
cat docker-compose.yml | grep -E "^  [a-z-]+:" | head -10
```

### ステップ3: webサービスを起動

webサービスが起動していない場合：

```bash
cd /var/www/toybox/backend

# webサービスを起動
docker compose up -d web

# または、すべてのサービスを起動
docker compose up -d

# サービスが起動するまで待つ
sleep 10

# サービス状態を確認
docker compose ps
```

### ステップ4: webサービスのコンテナIDを取得

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得（複数の方法を試す）
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID (method 1): $WEB_CONTAINER_ID"

# サービス名が異なる場合、docker-compose.ymlを確認
cat docker-compose.yml | grep -E "^  [a-z-]+:" | head -10

# 実際のコンテナ名で検索
docker ps | grep -E "backend|toybox" | grep -v caddy
```

### ステップ5: webサービスをbackend_defaultネットワークに接続

```bash
cd /var/www/toybox/backend

# webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)

# コンテナIDが取得できない場合、コンテナ名で検索
if [ -z "$WEB_CONTAINER_ID" ]; then
    echo "Trying to find web service by container name..."
    WEB_CONTAINER_ID=$(docker ps | grep -E "backend.*web|toybox.*web" | awk '{print $1}' | head -1)
    echo "Web container ID (method 2): $WEB_CONTAINER_ID"
fi

# コンテナIDが取得できた場合、ネットワークに接続
if [ ! -z "$WEB_CONTAINER_ID" ]; then
    echo "Connecting web service to backend_default network..."
    docker network connect backend_default $WEB_CONTAINER_ID
    
    # 接続を確認
    docker network inspect backend_default | grep -E "caddy|web" -A 5
else
    echo "ERROR: Could not find web service container"
    echo "Please check docker-compose.yml for the correct service name"
fi
```

---

## 一括確認コマンド

以下のコマンドを順番に実行してください：

```bash
# 1. すべてのサービスを確認
cd /var/www/toybox/backend
echo "=== All services ==="
docker compose ps

# 2. すべてのサービス（停止中も含む）を確認
echo "=== All services (including stopped) ==="
docker compose ps -a

# 3. docker-compose.ymlのサービス名を確認
echo "=== Service names in docker-compose.yml ==="
cat docker-compose.yml | grep -E "^  [a-z-]+:" | head -10

# 4. 実行中のコンテナを確認
echo "=== Running containers ==="
docker ps | grep -E "backend|toybox"

# 5. webサービスを起動（起動していない場合）
echo "=== Starting web service ==="
docker compose up -d web

# 6. サービスが起動するまで待つ
sleep 10

# 7. webサービスのコンテナIDを取得
WEB_CONTAINER_ID=$(docker compose ps -q web)
echo "Web container ID: $WEB_CONTAINER_ID"

# 8. コンテナIDが取得できない場合、コンテナ名で検索
if [ -z "$WEB_CONTAINER_ID" ]; then
    echo "Trying to find web service by container name..."
    WEB_CONTAINER_ID=$(docker ps | grep -E "backend.*web|toybox.*web" | awk '{print $1}' | head -1)
    echo "Web container ID (method 2): $WEB_CONTAINER_ID"
fi

# 9. webサービスをbackend_defaultネットワークに接続
if [ ! -z "$WEB_CONTAINER_ID" ]; then
    echo "=== Connecting web service to backend_default ==="
    docker network connect backend_default $WEB_CONTAINER_ID
    
    # 接続を確認
    echo "=== Verifying connection ==="
    docker network inspect backend_default | grep -E "caddy|web" -A 5
    
    # webサービスを再起動
    echo "=== Restarting web service ==="
    docker restart $WEB_CONTAINER_ID
    
    # DNS解決を確認
    echo "=== Testing DNS resolution ==="
    sleep 5
    cd /var/www/toybox
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web
else
    echo "ERROR: Could not find web service container"
    echo "Please check the service name in docker-compose.yml"
fi
```

---

## トラブルシューティング

### 問題1: webサービスが起動していない

```bash
cd /var/www/toybox/backend

# webサービスを起動
docker compose up -d --build web

# webサービスのログを確認
docker compose logs web --tail=50
```

### 問題2: サービス名が`web`でない

`backend/docker-compose.yml`でサービス名を確認：

```bash
cd /var/www/toybox/backend

# docker-compose.ymlのサービス名を確認
cat docker-compose.yml | grep -E "^  [a-z-]+:" | head -10

# 実際のサービス名を使用してコンテナIDを取得
# 例: サービス名が`django`の場合
DJANGO_CONTAINER_ID=$(docker compose ps -q django)
echo "Django container ID: $DJANGO_CONTAINER_ID"
```

### 問題3: コンテナが見つからない

```bash
# すべてのコンテナを確認
docker ps -a | grep -E "backend|toybox"

# コンテナ名で直接指定
# 例: コンテナ名が`backend-web-1`の場合
docker network connect backend_default backend-web-1
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ webサービスが起動している
2. ✅ webサービスのコンテナIDが取得できる
3. ✅ webサービスが`backend_default`ネットワークに接続されている
4. ✅ DNS解決ができる（`nslookup web`でIPアドレスが返る）
