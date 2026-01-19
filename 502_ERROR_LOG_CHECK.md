# 502エラーの原因特定 - ログ確認ポイント

## 502エラーの原因を特定するための確認箇所

502 Bad Gatewayエラーが続いている場合、以下の順番でログを確認してください。

---

## 1. Caddyのログを確認（最重要）

Caddyがリバースプロキシとして動作しているため、まずCaddyのログを確認します。

### コマンド

```bash
cd /var/www/toybox

# Caddyのログを確認（最新100行）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=100

# エラーメッセージを検索
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i "error\|502\|bad gateway\|connection\|refused"

# リアルタイムでログを確認（ブラウザでアクセスしながら）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy
```

### 確認ポイント

- **`dial tcp: lookup web on ...: no such host`** → サービス名が間違っている、またはネットワークに接続されていない
- **`dial tcp ...:8000: connect: connection refused`** → webサービスが起動していない、またはポートが間違っている
- **`upstream connect error or disconnect/reset before headers`** → webサービスがクラッシュしている、またはタイムアウトしている
- **`context deadline exceeded`** → タイムアウトが発生している

---

## 2. webサービス（Django）のログを確認

webサービスが正常に動作しているか確認します。

### コマンド

```bash
cd /var/www/toybox/backend

# webサービスのログを確認（最新100行）
docker compose logs web --tail=100

# エラーメッセージを検索
docker compose logs web | grep -i "error\|exception\|failed\|traceback"

# リアルタイムでログを確認
docker compose logs -f web
```

### 確認ポイント

- **`OperationalError: could not connect to server`** → データベース接続エラー
- **`ConnectionRefusedError`** → Redis接続エラー
- **`ModuleNotFoundError`** → Pythonモジュールのインポートエラー
- **`django.core.exceptions.ImproperlyConfigured`** → 設定エラー
- **`OSError: [Errno 98] Address already in use`** → ポート8000が既に使用されている

---

## 3. webサービスの状態を確認

webサービスが起動しているか、正常に動作しているか確認します。

### コマンド

```bash
cd /var/www/toybox/backend

# webサービスの状態を確認
docker compose ps

# webサービスがUp状態か確認
docker compose ps | grep web

# webサービスの詳細情報を確認
docker compose ps web --format json | jq .

# webサービスコンテナの状態を確認
docker inspect $(docker compose ps -q web) | grep -A 10 "State"
```

### 確認ポイント

- **`Status: Exit 1`** → webサービスがクラッシュしている
- **`Status: Restarting`** → webサービスが繰り返し再起動している（クラッシュループ）
- **`Status: Up`** → webサービスは起動しているが、リクエストに応答できない可能性がある

---

## 4. webサービスに直接接続できるか確認

webサービスが正常に応答するか確認します。

### コマンド

```bash
cd /var/www/toybox/backend

# webサービスコンテナ内からヘルスチェック
docker compose exec web curl -v http://localhost:8000/api/health/

# ホストから直接接続（ポート8000が公開されている場合）
curl -v http://localhost:8000/api/health/

# webサービスコンテナのIPアドレスを確認
docker compose exec web hostname -i
```

### 確認ポイント

- **`Connection refused`** → webサービスが起動していない、またはポート8000でリッスンしていない
- **`HTTP/1.1 200 OK`** → webサービスは正常に動作している
- **`HTTP/1.1 500 Internal Server Error`** → webサービスは起動しているが、エラーが発生している

---

## 5. Caddyからwebサービスに接続できるか確認

Caddyコンテナからwebサービスに接続できるか確認します。

### コマンド

```bash
cd /var/www/toybox

# Caddyコンテナ内からwebサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl -v http://web:8000/api/health/

# または、wgetを使用
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy wget -O- http://web:8000/api/health/

# Caddyコンテナ内からDNS解決を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy nslookup web
```

### 確認ポイント

- **`could not resolve host: web`** → DNS解決できない（ネットワークに接続されていない）
- **`Connection refused`** → webサービスに接続できない
- **`HTTP/1.1 200 OK`** → Caddyからwebサービスに接続できる

---

## 6. Dockerネットワークを確認

Caddyとwebサービスが同じネットワークに接続されているか確認します。

### コマンド

```bash
# Dockerネットワーク一覧を確認
docker network ls

# backend_defaultネットワークの詳細を確認
docker network inspect backend_default

# Caddyとwebサービスが同じネットワークに接続されているか確認
docker network inspect backend_default | grep -E "caddy|web" -A 5

# Caddyコンテナのネットワーク設定を確認
docker inspect $(docker ps -q --filter "ancestor=caddy") | grep -A 20 "Networks"

# webサービスのネットワーク設定を確認
cd /var/www/toybox/backend
docker inspect $(docker compose ps -q web) | grep -A 20 "Networks"
```

### 確認ポイント

- **Caddyとwebサービスが同じネットワーク（`backend_default`）に接続されているか**
- **ネットワークが存在するか**（`docker network ls`で確認）

---

## 7. Caddyfileの設定を確認

Caddyfileの設定が正しいか確認します。

### コマンド

```bash
cd /var/www/toybox

# Caddyfileの内容を確認
cat Caddyfile

# web:8000を参照しているか確認
grep -n "web:8000" Caddyfile

# Caddyfileの構文を確認
docker run --rm -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2 caddy validate --config /etc/caddy/Caddyfile

# backend/docker-compose.ymlのサービス名を確認
cat backend/docker-compose.yml | grep -A 5 "web:"
```

### 確認ポイント

- **Caddyfileで`web:8000`を参照しているか**（`frontend:3000`や`backend:4000`ではないか）
- **ポート番号が`8000`か**（`backend/docker-compose.yml`で確認）
- **サービス名が`web`か**（`backend/docker-compose.yml`で確認）

---

## 8. ポートの状態を確認

ポート80/443と8000が正しく使用されているか確認します。

### コマンド

```bash
# ポート80/443を使用しているプロセスを確認
sudo netstat -tlnp | grep -E ':80|:443'

# ポート8000を使用しているプロセスを確認
sudo netstat -tlnp | grep ':8000'

# Dockerコンテナがポートを使用しているか確認
docker ps | grep -E '80|443|8000'

# ポート80/443がCaddyコンテナに割り当てられているか確認
docker ps --filter "ancestor=caddy" --format "table {{.Names}}\t{{.Ports}}"
```

### 確認ポイント

- **ポート80/443がCaddyコンテナに割り当てられているか**
- **ポート8000がwebサービスに割り当てられているか**
- **システムレベルのnginxがポート80/443を占有していないか**

---

## 9. データベースとRedisの接続を確認

webサービスがデータベースとRedisに接続できるか確認します。

### コマンド

```bash
cd /var/www/toybox/backend

# データベース接続を確認
docker compose exec web python manage.py check --database default

# Redis接続を確認
docker compose exec web python -c "import redis; r = redis.Redis.from_url('redis://redis:6379/0'); print(r.ping())"

# 環境変数を確認
docker compose exec web env | grep -E "DB_|REDIS_"
```

### 確認ポイント

- **データベース接続エラーがないか**
- **Redis接続エラーがないか**
- **環境変数が正しく設定されているか**

---

## 10. システムリソースを確認

サーバーのリソースが不足していないか確認します。

### コマンド

```bash
# CPUとメモリの使用状況を確認
top
# または
htop

# ディスク容量を確認
df -h

# Dockerコンテナのリソース使用状況を確認
docker stats --no-stream
```

### 確認ポイント

- **メモリが不足していないか**
- **ディスク容量が不足していないか**
- **CPU使用率が異常に高くないか**

---

## ログ収集コマンド（問題報告用）

問題を報告する際に、以下のコマンドの出力を収集してください：

```bash
# 1. Caddyのログ（最新100行）
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=100 > caddy_logs.txt

# 2. webサービスのログ（最新100行）
cd /var/www/toybox/backend
docker compose logs web --tail=100 > web_logs.txt

# 3. コンテナの状態
docker compose ps > container_status.txt
cd ..
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps > caddy_status.txt

# 4. ネットワーク情報
docker network inspect backend_default > network_info.txt

# 5. Caddyfileの内容
cat Caddyfile > caddyfile_content.txt

# 6. docker-compose.prod.ymlの内容
cat docker-compose.prod.yml > docker_compose_prod.txt
```

---

## よくある原因と対処法

### 原因1: webサービスが起動していない

**症状**: `docker compose ps | grep web`で`Exit`状態

**対処法**:
```bash
cd /var/www/toybox/backend
docker compose logs web  # エラーの原因を確認
docker compose up -d --build web  # 再起動
```

### 原因2: Caddyとwebサービスが異なるネットワークに接続されている

**症状**: `docker network inspect backend_default`でCaddyまたはwebサービスが表示されない

**対処法**:
```bash
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

### 原因3: Caddyfileの設定が間違っている

**症状**: Caddyfileで`frontend:3000`や`backend:4000`を参照している

**対処法**: Caddyfileを`web:8000`を参照するように修正（`502_BAD_GATEWAY_FIX.md`の「方法C」を参照）

### 原因4: webサービスがクラッシュしている

**症状**: `docker compose logs web`でエラーメッセージが表示される

**対処法**: エラーメッセージに応じて対処（データベース接続エラーの場合、データベースを確認）

---

## 次のステップ

1. 上記のコマンドを順番に実行して、ログを確認してください
2. エラーメッセージを特定してください
3. 該当する「よくある原因と対処法」を参照してください
4. それでも解決しない場合、ログ収集コマンドの出力を確認して、さらに詳しく調査します
