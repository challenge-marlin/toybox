# Caddy起動後の確認手順

## Caddyコンテナを起動した後の確認事項

### ステップ1: Caddyコンテナの状態を確認

```bash
cd /var/www/toybox

# Caddyコンテナが起動しているか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# または、直接確認
docker ps | grep caddy

# Caddyコンテナの詳細を確認
docker ps --filter "ancestor=caddy" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**確認ポイント**:
- Caddyコンテナが`Up`状態か
- ポート80/443が割り当てられているか（`0.0.0.0:80->80/tcp`など）

### ステップ2: webサービス（backend）が起動しているか確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps

# webサービスがUp状態か確認
docker compose ps | grep web
```

**確認ポイント**:
- webサービスが`Up`状態か
- ポート8000でリッスンしているか

### ステップ3: Dockerネットワークを確認

```bash
# Dockerネットワーク一覧を確認
docker network ls

# backend_defaultネットワークを確認
docker network inspect backend_default | grep -A 10 "Containers"

# Caddyとwebサービスが同じネットワークに接続されているか確認
docker network inspect backend_default | grep -E "caddy|web"
```

**確認ポイント**:
- Caddyコンテナとwebサービスが同じネットワーク（`backend_default`）に接続されているか

### ステップ4: Caddyのログを確認

```bash
cd /var/www/toybox

# Caddyのログを確認（最新50行）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=50

# エラーがないか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i error

# リアルタイムでログを確認（Ctrl+Cで終了）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy
```

**確認ポイント**:
- エラーメッセージがないか
- Caddyが正常に起動しているか
- webサービスに接続できているか

### ステップ5: webサービスに直接接続できるか確認

```bash
cd /var/www/toybox/backend

# webサービスコンテナ内からヘルスチェック
docker compose exec web curl http://localhost:8000/api/health/

# または、ホストから直接接続（ポート8000が公開されている場合）
curl http://localhost:8000/api/health/
```

**確認ポイント**:
- webサービスが正常に応答するか

### ステップ6: Caddyからwebサービスに接続できるか確認

```bash
cd /var/www/toybox

# Caddyコンテナ内からwebサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy wget -O- http://web:8000/api/health/

# または、curlを使用
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl http://web:8000/api/health/
```

**確認ポイント**:
- Caddyコンテナからwebサービスに接続できるか

### ステップ7: ポート80/443の状態を確認

```bash
# ポート80/443を使用しているプロセスを確認
sudo netstat -tlnp | grep -E ':80|:443'

# または
sudo ss -tlnp | grep -E ':80|:443'

# Dockerコンテナがポートを使用しているか確認
docker ps | grep -E '80|443'
```

**確認ポイント**:
- ポート80/443がCaddyコンテナに割り当てられているか
- システムレベルのnginxがポートを占有していないか

### ステップ8: 実際にアクセステスト

```bash
# ローカルからHTTPでテスト
curl -I http://toybox.ayatori-inc.co.jp

# HTTPSでテスト
curl -I https://toybox.ayatori-inc.co.jp

# ヘルスチェックエンドポイントをテスト
curl http://toybox.ayatori-inc.co.jp/health

# APIエンドポイントをテスト
curl http://toybox.ayatori-inc.co.jp/api/health/
```

**確認ポイント**:
- サイトにアクセスできるか
- 502エラーやERR_CONNECTION_REFUSEDエラーが発生しないか

---

## 問題が発生した場合の対処法

### 問題1: Caddyコンテナが起動しない

```bash
cd /var/www/toybox

# Caddyのログを詳細に確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# Caddyfileの構文を確認
docker run --rm -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2 caddy validate --config /etc/caddy/Caddyfile

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

### 問題2: webサービスに接続できない

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps | grep web

# webサービスのログを確認
docker compose logs web --tail=50

# webサービスを再起動
docker compose restart web

# または、再作成
docker compose up -d --force-recreate web
```

### 問題3: Caddyとwebサービスが異なるネットワークに接続されている

```bash
# ネットワークを確認
docker network inspect backend_default | grep -E "caddy|web"

# Caddyコンテナのネットワークを確認
docker inspect $(docker ps -q --filter "ancestor=caddy") | grep -A 10 "Networks"

# webサービスのネットワークを確認
cd /var/www/toybox/backend
docker inspect $(docker compose ps -q web) | grep -A 10 "Networks"
```

**解決策**: `docker-compose.prod.yml`で`backend_default`ネットワークを指定しているか確認してください。

### 問題4: ポート80/443が既に使用されている

```bash
# ポート80/443を使用しているプロセスを確認
sudo lsof -i :80
sudo lsof -i :443

# システムレベルのnginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo pkill -9 nginx

# ポートが解放されたか確認
sudo netstat -tlnp | grep -E ':80|:443'
```

---

## 確認チェックリスト

以下の項目を確認してください：

- [ ] Caddyコンテナが`Up`状態で起動している
- [ ] webサービスが`Up`状態で起動している
- [ ] Caddyとwebサービスが同じネットワーク（`backend_default`）に接続されている
- [ ] ポート80/443がCaddyコンテナに割り当てられている
- [ ] Caddyのログにエラーがない
- [ ] Caddyからwebサービスに接続できる
- [ ] `curl http://toybox.ayatori-inc.co.jp`でアクセスできる
- [ ] 502エラーやERR_CONNECTION_REFUSEDエラーが発生しない

---

## 次のステップ

すべての確認が完了したら：

1. **ブラウザでアクセス**: `http://toybox.ayatori-inc.co.jp` または `https://toybox.ayatori-inc.co.jp`
2. **SSO処理をテスト**: SSOログインを試行して、502エラーが発生しないか確認
3. **ログを監視**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy`でリアルタイムログを確認
