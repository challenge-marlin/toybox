# SSO 502エラー 緊急修正手順

## 問題の原因

`backend/docker-compose.yml`にnginxサービスが定義されていないため、システムレベルのnginxがポート80をリッスンしていますが、Dockerコンテナのwebサービス（`web:8000`）に接続できていません。

## 緊急対応手順

### ステップ1: システムレベルのnginxを停止

サーバー側でSSH接続またはWinSCPのターミナル機能を使用：

```bash
# nginxを停止
sudo systemctl stop nginx

# nginxを無効化（再起動時に自動起動しないようにする）
sudo systemctl disable nginx

# nginxプロセスが残っていないか確認
ps aux | grep nginx

# 残っているプロセスを強制終了
sudo pkill -9 nginx

# ポート80/443が解放されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
```

### ステップ2: docker-compose.ymlを更新

**WinSCPでアップロード**:
- **ローカル**: `C:\github\toybox\backend\docker-compose.yml`
- **サーバー**: `/home/app/toybox/backend/docker-compose.yml`

**変更内容**: nginxサービスを追加（既に修正済み）

### ステップ3: Dockerコンテナを再起動

サーバー側で実行：

```bash
# プロジェクトディレクトリに移動
cd /home/app/toybox/backend
# または
cd /root/toybox/backend

# コンテナを停止
docker compose down

# コンテナを再起動
docker compose up -d --build

# コンテナの状態を確認
docker compose ps

# nginxサービスが起動しているか確認
docker compose ps | grep nginx

# webサービスのログを確認
docker compose logs web --tail=50
```

### ステップ4: 動作確認

```bash
# ヘルスチェックエンドポイントを確認
curl http://localhost/api/health/

# または、サーバーのIPアドレスから
curl http://<サーバーIP>/api/health/
```

---

## 代替案: webサービスに直接アクセス（一時的）

nginxサービスを追加する前に、一時的にwebサービスに直接アクセスする方法：

```bash
# 1. nginxを停止（上記のステップ1を実行）

# 2. webサービスがポート8000でリッスンしているか確認
docker compose ps | grep "8000:8000"

# 3. 直接アクセスをテスト
curl http://localhost:8000/api/health/
curl http://<サーバーIP>:8000/api/health/
```

**注意**: この方法は一時的な確認用です。本番環境ではnginxサービスを使用してください。

---

## トラブルシューティング

### nginxサービスが起動しない場合

```bash
# nginxサービスのログを確認
docker compose logs nginx

# nginx設定ファイルの構文を確認
docker compose exec nginx nginx -t

# nginx設定ファイルの内容を確認
docker compose exec nginx cat /etc/nginx/conf.d/default.conf
```

### webサービスに接続できない場合

```bash
# webサービスが起動しているか確認
docker compose ps | grep web

# webサービスのログを確認
docker compose logs web --tail=100

# webサービスに直接接続テスト
docker compose exec web curl http://localhost:8000/api/health/

# Dockerネットワークを確認
docker network inspect backend_default | grep -A 5 "web\|nginx"
```

### ポート80が既に使用されている場合

```bash
# ポート80を使用しているプロセスを確認
sudo lsof -i :80
sudo netstat -tlnp | grep :80

# プロセスを停止
sudo systemctl stop <サービス名>
# または
sudo kill -9 <PID>
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ nginxサービスが起動している（`docker compose ps | grep nginx`）
2. ✅ webサービスが起動している（`docker compose ps | grep web`）
3. ✅ ポート80でアクセスできる（`curl http://localhost/api/health/`）
4. ✅ SSO処理が正常に動作する（ブラウザでSSOログインを試行）

---

## 参考資料

- `SSO_502_DETAILED_DIAGNOSIS.md` - 詳細な診断手順
- `SSO_502_ERROR_FIX.md` - 一般的な解決手順
- `SSO_FIX_UPLOAD_LIST.md` - WinSCPアップロードファイルリスト
