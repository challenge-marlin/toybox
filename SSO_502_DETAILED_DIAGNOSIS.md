# SSO 502エラー詳細診断手順

## 緊急診断コマンド（サーバー側で実行）

以下のコマンドを順番に実行して、問題を特定してください。

### 1. システムレベルのnginxの状態を確認

```bash
# nginxが動いているか確認
sudo systemctl status nginx

# nginxプロセスを確認
ps aux | grep nginx

# ポート80/443が使用されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
# または
sudo ss -tlnp | grep -E ':80|:443'
```

**確認ポイント**:
- nginxが動いている場合、それが502エラーの原因です
- ポート80がnginxに占有されている場合、Dockerコンテナのwebサービスに接続できません

### 2. Dockerコンテナの状態を確認

```bash
# プロジェクトディレクトリに移動
cd /home/app/toybox/backend
# または
cd /root/toybox/backend

# Dockerコンテナの状態を確認
docker compose ps

# webサービスが起動しているか確認
docker compose ps | grep web

# webサービスのログを確認（最新50行）
docker compose logs web --tail=50

# webサービスがエラーで停止していないか確認
docker compose logs web | grep -i "error\|exception\|failed\|started"
```

**確認ポイント**:
- webサービスが`Up`状態か確認
- webサービスがクラッシュしていないか確認
- エラーログがないか確認

### 3. webサービスに直接接続できるか確認

```bash
# webサービスコンテナ内からヘルスチェック
docker compose exec web curl http://localhost:8000/api/health/

# または、ホストから直接接続（ポート8000が公開されている場合）
curl http://localhost:8000/api/health/

# webサービスのIPアドレスを確認
docker compose exec web hostname -i
```

**確認ポイント**:
- webサービスが正常に応答するか確認
- ポート8000でリッスンしているか確認

### 4. nginx設定ファイルの場所を確認

```bash
# システムレベルのnginx設定ファイルを確認
sudo nginx -t
sudo cat /etc/nginx/sites-enabled/default
sudo cat /etc/nginx/nginx.conf | grep -A 10 "server"

# Dockerコンテナ内のnginx設定ファイルを確認（nginxコンテナがある場合）
docker compose exec nginx cat /etc/nginx/conf.d/default.conf
```

**確認ポイント**:
- どのnginx設定ファイルが使用されているか確認
- upstream設定が正しいか確認（`server web:8000;`になっているか）

### 5. Dockerネットワークを確認

```bash
# Dockerネットワーク一覧を確認
docker network ls

# backend_defaultネットワークを確認
docker network inspect backend_default

# webサービスがネットワークに接続されているか確認
docker network inspect backend_default | grep -A 5 "web"
```

**確認ポイント**:
- webサービスがDockerネットワークに接続されているか確認
- nginxが同じネットワークに接続されているか確認

### 6. SSO処理のログを確認

```bash
# SSO関連のログを確認
docker compose logs web | grep -i "sso\|SSO" | tail -30

# エラーログを確認
docker compose logs web | grep -i "error\|exception\|timeout" | tail -30

# 最新のログをリアルタイムで確認
docker compose logs web -f
```

**確認ポイント**:
- SSO処理中にエラーが発生しているか確認
- タイムアウトエラーが発生しているか確認

---

## 問題別の解決手順

### 問題A: システムレベルのnginxが動いている

**症状**: `sudo systemctl status nginx`でnginxが`active (running)`になっている

**解決手順**:

```bash
# 1. nginxを停止
sudo systemctl stop nginx

# 2. nginxを無効化（再起動時に自動起動しないようにする）
sudo systemctl disable nginx

# 3. nginxプロセスが残っていないか確認
ps aux | grep nginx

# 4. 残っているプロセスを強制終了
sudo pkill -9 nginx

# 5. ポート80/443が解放されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
```

### 問題B: webサービスが起動していない、またはクラッシュしている

**症状**: `docker compose ps`でwebサービスが`Exit`状態になっている

**解決手順**:

```bash
# 1. webサービスのログを確認
docker compose logs web

# 2. エラーの原因を特定
docker compose logs web | grep -i "error\|exception\|failed"

# 3. webサービスを再起動
docker compose restart web

# 4. まだ起動しない場合、コンテナを再作成
docker compose up -d --force-recreate web

# 5. データベース接続エラーの場合
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate
```

### 問題C: nginxがwebサービスに接続できない（Dockerネットワークの問題）

**症状**: nginx設定ファイルの`upstream django { server web:8000; }`が正しく動作していない

**解決手順**:

```bash
# 1. nginxサービスがdocker-compose.ymlに定義されているか確認
cat docker-compose.yml | grep -A 10 nginx

# 2. nginxサービスが定義されていない場合、追加する必要があります
# （後述の「nginxサービスを追加する方法」を参照）

# 3. nginxサービスが定義されている場合、同じネットワークに接続されているか確認
docker network inspect backend_default | grep -A 5 "nginx\|web"

# 4. nginxサービスを再起動
docker compose restart nginx
```

### 問題D: SSO処理でタイムアウトが発生している

**症状**: SSO処理中にタイムアウトエラーが発生している

**解決手順**:

```bash
# 1. SSO関連の環境変数が正しく設定されているか確認
docker compose exec web env | grep SSO

# 2. SSO APIへの接続をテスト
docker compose exec web curl -v --max-time 30 <SSO_API_BASE_URL>/api/sso/ticket/verify

# 3. タイムアウト設定を確認（既に30秒に延長済み）
docker compose exec web grep -n "DEFAULT_TIMEOUT_SECONDS" sso_integration/services.py

# 4. nginx設定のタイムアウトを確認（既に90秒に延長済み）
cat nginx/conf/default.conf | grep timeout
```

---

## nginxサービスをdocker-compose.ymlに追加する方法

現在、`backend/docker-compose.yml`にnginxサービスが定義されていない可能性があります。以下の手順で追加してください。

### ステップ1: docker-compose.ymlを編集

`backend/docker-compose.yml`に以下を追加：

```yaml
services:
  # ... 既存のサービス（db, redis, web, worker, beat）...

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf/default.conf:/etc/nginx/conf.d/default.conf:ro
      - static_volume:/app/staticfiles:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - default
```

### ステップ2: システムレベルのnginxを停止

```bash
sudo systemctl stop nginx
sudo systemctl disable nginx
```

### ステップ3: Dockerコンテナを再起動

```bash
cd /home/app/toybox/backend
docker compose down
docker compose up -d --build
docker compose ps
```

---

## 緊急対応: システムレベルのnginxを停止してwebサービスに直接アクセス

502エラーが続く場合、一時的にシステムレベルのnginxを停止して、webサービスに直接アクセスできるか確認してください。

```bash
# 1. nginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx

# 2. webサービスがポート8000でリッスンしているか確認
docker compose ps
docker compose logs web | tail -20

# 3. ポート8000が公開されているか確認
docker compose ps | grep "8000:8000"

# 4. 直接アクセスをテスト
curl http://localhost:8000/api/health/
curl http://<サーバーIP>:8000/api/health/
```

**注意**: この方法は一時的な確認用です。本番環境ではnginxまたはCaddyなどのリバースプロキシを使用する必要があります。

---

## ログ収集コマンド（問題報告用）

問題を報告する際に、以下のコマンドの出力を収集してください：

```bash
# 1. システム情報
uname -a
docker --version
docker compose version

# 2. nginxの状態
sudo systemctl status nginx
ps aux | grep nginx
sudo netstat -tlnp | grep -E ':80|:443'

# 3. Dockerコンテナの状態
cd /home/app/toybox/backend
docker compose ps
docker compose ps -a

# 4. webサービスのログ
docker compose logs web --tail=100

# 5. ネットワーク情報
docker network ls
docker network inspect backend_default

# 6. SSO関連のログ
docker compose logs web | grep -i "sso\|SSO" | tail -50
docker compose logs web | grep -i "error\|exception\|timeout" | tail -50
```

---

## 次のステップ

1. 上記の診断コマンドを実行して、問題を特定してください
2. 問題が特定できたら、該当する「問題別の解決手順」を実行してください
3. それでも解決しない場合、ログ収集コマンドの出力を確認して、さらに詳しく調査します
