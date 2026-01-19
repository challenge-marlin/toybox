# ERR_CONNECTION_REFUSED エラー解決手順

## 問題の概要
`toybox.ayatori-inc.co.jp`にアクセスすると「ERR_CONNECTION_REFUSED」エラーが発生し、接続できない状態。

## 原因の可能性
1. **Caddyコンテナが起動していない**（最も可能性が高い）
2. **ポート80/443が開いていない、またはファイアウォールでブロックされている**
3. **システムレベルのnginxがポート80/443を占有している**
4. **Dockerコンテナが起動していない**
5. **docker-compose.prod.ymlが存在しない、またはCaddyサービスが定義されていない**

## 緊急診断コマンド（サーバー側で実行）

### ステップ1: サーバーに接続（VNCコンソールまたはSSH）

ConoHa管理画面 → VNCコンソール → rootユーザーでログイン

### ステップ2: Dockerコンテナの状態を確認

```bash
# プロジェクトディレクトリを探す
find / -name "Caddyfile" -type f 2>/dev/null
# または
ls -la /home/app/toybox
ls -la /root/toybox

# プロジェクトディレクトリに移動
cd /home/app/toybox
# または
cd /root/toybox

# Dockerコンテナの状態を確認
docker compose ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps 2>/dev/null

# すべてのDockerコンテナを確認
docker ps -a
```

**確認ポイント**:
- Caddyコンテナが起動しているか（`Up`状態か）
- ポート80/443がCaddyコンテナに割り当てられているか

### ステップ3: ポート80/443の状態を確認

```bash
# ポート80/443を使用しているプロセスを確認
sudo netstat -tlnp | grep -E ':80|:443'
# または
sudo ss -tlnp | grep -E ':80|:443'

# Dockerコンテナがポートを使用しているか確認
docker ps | grep -E '80|443'
```

**確認ポイント**:
- ポート80/443が使用されているか
- どのプロセスが使用しているか（nginx、Caddy、その他）

### ステップ4: システムレベルのnginxの状態を確認

```bash
# nginxが動いているか確認
sudo systemctl status nginx

# nginxプロセスを確認
ps aux | grep nginx

# nginxが動いている場合は停止
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo pkill -9 nginx
```

### ステップ5: Caddyfileとdocker-compose.prod.ymlの存在確認

```bash
# プロジェクトディレクトリに移動
cd /home/app/toybox
# または
cd /root/toybox

# Caddyfileが存在するか確認
ls -la Caddyfile
cat Caddyfile

# docker-compose.prod.ymlが存在するか確認
ls -la docker-compose.prod.yml
cat docker-compose.prod.yml | grep -A 10 caddy
```

**確認ポイント**:
- Caddyfileが存在するか
- docker-compose.prod.ymlが存在するか
- Caddyサービスが定義されているか

### ステップ6: Caddyコンテナのログを確認

```bash
# Caddyコンテナのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=50

# または、コンテナ名で直接確認
docker logs $(docker ps -q --filter "ancestor=caddy") 2>/dev/null
```

**確認ポイント**:
- Caddyが起動しているか
- エラーメッセージがないか
- ポート80/443でリッスンしているか

---

## 解決手順

### 方法A: Caddyコンテナを起動（推奨）

#### ステップ1: システムレベルのnginxを停止

```bash
# nginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo pkill -9 nginx

# ポート80/443が解放されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
```

#### ステップ2: docker-compose.prod.ymlを確認・作成

**docker-compose.prod.ymlが存在しない場合、作成する必要があります。**

プロジェクトのルートディレクトリ（`Caddyfile`がある場所）に`docker-compose.prod.yml`を作成：

```yaml
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
    depends_on:
      - frontend
      - backend
    networks:
      - default

volumes:
  caddy-data:
  caddy-config:
```

**注意**: `frontend`と`backend`サービスが`docker-compose.yml`に定義されている必要があります。

#### ステップ3: Dockerコンテナを起動

```bash
# プロジェクトディレクトリに移動
cd /home/app/toybox
# または
cd /root/toybox

# コンテナを停止（既存のコンテナがある場合）
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# コンテナを起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy
```

#### ステップ4: 動作確認

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# Caddyコンテナがポート80/443でリッスンしているか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps caddy
```

### 方法B: 一時的にnginxサービスを使用（backend/docker-compose.yml）

`backend/docker-compose.yml`にnginxサービスが追加されている場合、一時的にこれを使用することもできます。

```bash
# backendディレクトリに移動
cd /home/app/toybox/backend
# または
cd /root/toybox/backend

# システムレベルのnginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx

# Dockerコンテナを起動
docker compose up -d --build

# コンテナの状態を確認
docker compose ps
```

**注意**: この方法は一時的な対応です。本番環境ではCaddyを使用することを推奨します。

### 方法C: ファイアウォールの確認

```bash
# ファイアウォールの状態を確認（Ubuntu/Debian）
sudo ufw status

# ポート80/443が開いているか確認
sudo ufw status | grep -E '80|443'

# ポート80/443を開く（閉じている場合）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload

# ファイアウォールの状態を確認（CentOS/RHEL）
sudo firewall-cmd --list-all

# ポート80/443を開く（CentOS/RHEL）
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## トラブルシューティング

### 問題1: docker-compose.prod.ymlが存在しない

**解決策**: 上記の「方法A: ステップ2」を参照して、`docker-compose.prod.yml`を作成してください。

### 問題2: Caddyコンテナが起動しない

```bash
# Caddyのログを詳細に確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# Caddyfileの構文を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

### 問題3: ポート80/443が既に使用されている

```bash
# ポート80/443を使用しているプロセスを確認
sudo lsof -i :80
sudo lsof -i :443

# プロセスを停止
sudo systemctl stop <サービス名>
# または
sudo kill -9 <PID>
```

### 問題4: frontend/backendサービスが存在しない

Caddyfileでは`frontend:3000`と`backend:4000`を参照していますが、これらのサービスが`docker-compose.yml`に定義されていない場合、Caddyが起動できません。

**解決策**: 
- `docker-compose.yml`に`frontend`と`backend`サービスを追加する
- または、Caddyfileを修正して既存のサービス（`web:8000`など）を参照する

---

## 確認事項

修正後、以下を確認してください：

1. ✅ Caddyコンテナが起動している（`docker compose ps | grep caddy`）
2. ✅ ポート80/443がCaddyコンテナに割り当てられている（`docker ps | grep caddy`）
3. ✅ ポート80/443でアクセスできる（`curl http://toybox.ayatori-inc.co.jp`）
4. ✅ システムレベルのnginxが停止している（`sudo systemctl status nginx`）

---

## ログ収集コマンド（問題報告用）

問題を報告する際に、以下のコマンドの出力を収集してください：

```bash
# 1. システム情報
uname -a
docker --version
docker compose version

# 2. ポートの状態
sudo netstat -tlnp | grep -E ':80|:443'
sudo ss -tlnp | grep -E ':80|:443'

# 3. nginxの状態
sudo systemctl status nginx
ps aux | grep nginx

# 4. Dockerコンテナの状態
cd /home/app/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker ps -a

# 5. Caddyのログ
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=100

# 6. Caddyfileの内容
cat Caddyfile

# 7. docker-compose.prod.ymlの内容
cat docker-compose.prod.yml
```

---

## 次のステップ

1. 上記の診断コマンドを実行して、問題を特定してください
2. 問題が特定できたら、該当する「解決手順」を実行してください
3. それでも解決しない場合、ログ収集コマンドの出力を確認して、さらに詳しく調査します
