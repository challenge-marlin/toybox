# サービス起動の問題を解決する手順

## 問題
`docker compose up -d`を実行してもサービスが起動しない、またはエラーが発生している可能性があります。

## 診断手順

### ステップ1: エラーメッセージを確認

```bash
cd /var/www/toybox/backend

# サービスを起動してエラーメッセージを確認
docker compose up -d

# エラーメッセージが表示された場合、その内容を確認
```

### ステップ2: サービスの状態を確認

```bash
cd /var/www/toybox/backend

# すべてのサービス（停止中も含む）を確認
docker compose ps -a

# サービスのログを確認
docker compose logs --tail=50
```

### ステップ3: 個別のサービスを起動

```bash
cd /var/www/toybox/backend

# dbサービスを起動
docker compose up -d db

# dbサービスのログを確認
docker compose logs db --tail=50

# redisサービスを起動
docker compose up -d redis

# redisサービスのログを確認
docker compose logs redis --tail=50

# webサービスを起動
docker compose up -d web

# webサービスのログを確認
docker compose logs web --tail=50
```

### ステップ4: 環境変数ファイルを確認

```bash
cd /var/www/toybox/backend

# .envファイルが存在するか確認
ls -la .env

# .envファイルの内容を確認（機密情報は表示されないように注意）
cat .env | head -20
```

### ステップ5: Dockerイメージを確認

```bash
cd /var/www/toybox/backend

# 必要なDockerイメージが存在するか確認
docker images | grep -E "postgres|redis|toybox"

# webサービスのイメージをビルド
docker compose build web
```

---

## 解決手順

### 方法A: サービスを個別に起動

```bash
cd /var/www/toybox/backend

# 1. dbサービスを起動
echo "=== Starting db service ==="
docker compose up -d db
sleep 10

# 2. redisサービスを起動
echo "=== Starting redis service ==="
docker compose up -d redis
sleep 10

# 3. webサービスを起動
echo "=== Starting web service ==="
docker compose up -d web
sleep 10

# 4. サービス状態を確認
echo "=== Service status ==="
docker compose ps
```

### 方法B: ログを確認して問題を特定

```bash
cd /var/www/toybox/backend

# すべてのサービスのログを確認
docker compose logs --tail=100

# エラーメッセージを検索
docker compose logs | grep -i error

# webサービスのログを確認
docker compose logs web --tail=100
```

### 方法C: サービスを再ビルドして起動

```bash
cd /var/www/toybox/backend

# サービスを再ビルド
docker compose build

# サービスを起動
docker compose up -d

# サービス状態を確認
docker compose ps
```

---

## 一括診断コマンド

以下のコマンドを順番に実行して、問題を特定してください：

```bash
# 1. 現在のサービス状態を確認
cd /var/www/toybox/backend
echo "=== Current service status ==="
docker compose ps -a

# 2. エラーメッセージを確認
echo "=== Checking for errors ==="
docker compose logs --tail=50 | grep -i error || echo "No errors found"

# 3. .envファイルの存在を確認
echo "=== Checking .env file ==="
if [ -f .env ]; then
    echo ".env file exists"
    ls -la .env
else
    echo "ERROR: .env file not found"
fi

# 4. Dockerイメージを確認
echo "=== Checking Docker images ==="
docker images | grep -E "postgres|redis|toybox" || echo "Images not found"

# 5. dbサービスを起動
echo "=== Starting db service ==="
docker compose up -d db
sleep 10
docker compose ps | grep db

# 6. redisサービスを起動
echo "=== Starting redis service ==="
docker compose up -d redis
sleep 10
docker compose ps | grep redis

# 7. webサービスを起動
echo "=== Starting web service ==="
docker compose up -d web
sleep 10
docker compose ps | grep web

# 8. すべてのサービスの状態を確認
echo "=== Final service status ==="
docker compose ps

# 9. webサービスのログを確認
echo "=== Web service logs ==="
docker compose logs web --tail=30
```

---

## トラブルシューティング

### 問題1: .envファイルが存在しない

```bash
cd /var/www/toybox/backend

# .envファイルのテンプレートを確認
ls -la .env.example 2>/dev/null || echo ".env.example not found"

# .envファイルを作成（必要に応じて）
# cp .env.example .env
# または、既存の.envファイルを確認
```

### 問題2: Dockerイメージが存在しない

```bash
cd /var/www/toybox/backend

# 必要なイメージをビルド
docker compose build

# または、個別にビルド
docker compose build web
```

### 問題3: ポートが既に使用されている

```bash
# ポート8000が使用されているか確認
netstat -tuln | grep 8000

# ポート5432が使用されているか確認
netstat -tuln | grep 5432

# ポート6379が使用されているか確認
netstat -tuln | grep 6379

# 使用されているポートを確認したら、docker-compose.ymlのポート設定を変更するか、既存のサービスを停止
```

### 問題4: ディレクトリやファイルが存在しない

```bash
cd /var/www/toybox/backend

# 必要なディレクトリが存在するか確認
ls -la nginx/conf/default.conf
ls -la public/uploads
ls -la backend/Dockerfile

# 存在しない場合は作成
mkdir -p nginx/conf
mkdir -p public/uploads
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ すべてのサービスが起動している（`docker compose ps`）
2. ✅ エラーメッセージがない（`docker compose logs`）
3. ✅ webサービスが起動している
4. ✅ webサービスが`backend_default`ネットワークに接続されている
