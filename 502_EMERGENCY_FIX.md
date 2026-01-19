# 502エラー緊急修正手順

## 緊急実行コマンド（順番に実行）

```bash
# 1. webサービスを強制再起動
cd /var/www/toybox/backend
docker compose restart web
sleep 10

# 2. webサービスが起動しているか確認
docker compose ps | grep web

# 3. webサービスに直接接続テスト
docker compose exec web curl http://localhost:8000/api/health/

# 4. Caddyfileを確認・更新（ローカルで修正済み）
cd /var/www/toybox
cat Caddyfile | head -20

# 5. CaddyコンテナのIDを取得
CADDY_ID=$(docker ps | grep caddy | awk '{print $1}')
echo "Caddy ID: $CADDY_ID"

# 6. Caddyをbackend_defaultネットワークに接続（強制）
docker network connect backend_default $CADDY_ID 2>/dev/null || echo "Already connected"

# 7. Caddyコンテナを再起動
docker restart $CADDY_ID
sleep 5

# 8. 接続テスト
docker exec $CADDY_ID curl -v http://web:8000/api/health/

# 9. Caddyのログを確認
docker logs $CADDY_ID --tail=30
```

## webサービスが起動しない場合

```bash
cd /var/www/toybox/backend

# ログを確認
docker compose logs web --tail=50

# 強制再作成
docker compose up -d --force-recreate web

# 状態確認
docker compose ps
```
