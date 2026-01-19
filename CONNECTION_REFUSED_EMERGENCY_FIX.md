# ERR_CONNECTION_REFUSED 緊急修正手順

## 問題
`toybox.ayatori-inc.co.jp`にアクセスすると「ERR_CONNECTION_REFUSED」エラーが発生。

## 最も可能性の高い原因
**Caddyコンテナが起動していない、またはポート80/443が開いていない**

## 緊急対応手順（サーバー側で実行）

### ステップ1: VNCコンソールでサーバーに接続

ConoHa管理画面 → VNCコンソール → rootユーザーでログイン

### ステップ2: プロジェクトディレクトリを確認

```bash
# Caddyfileを探す
find / -name "Caddyfile" -type f 2>/dev/null

# プロジェクトディレクトリに移動（見つかったパス）
cd /home/app/toybox
# または
cd /root/toybox

# 現在のディレクトリとファイルを確認
pwd
ls -la
```

### ステップ3: システムレベルのnginxを停止

```bash
# nginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo pkill -9 nginx

# ポート80/443が解放されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
```

### ステップ4: Dockerコンテナの状態を確認

```bash
# すべてのDockerコンテナを確認
docker ps -a

# Caddyコンテナがあるか確認
docker ps -a | grep caddy

# docker-compose.prod.ymlが存在するか確認
ls -la docker-compose.prod.yml
```

### ステップ5: docker-compose.prod.ymlが存在しない場合、作成

**プロジェクトのルートディレクトリ（Caddyfileがある場所）に`docker-compose.prod.yml`を作成：**

```bash
cat > docker-compose.prod.yml << 'EOF'
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
      - web
    networks:
      - default

volumes:
  caddy-data:
  caddy-config:
EOF
```

**注意**: Caddyfileでは`frontend:3000`と`backend:4000`を参照していますが、実際のサービス名は`web:8000`の可能性があります。Caddyfileを確認して、必要に応じて修正してください。

### ステップ6: Caddyfileを確認・修正

現在のCaddyfileは`frontend:3000`と`backend:4000`を参照していますが、実際のサービス名が異なる可能性があります。

```bash
# Caddyfileの内容を確認
cat Caddyfile

# backend/docker-compose.ymlのサービス名を確認
cat backend/docker-compose.yml | grep -A 5 "web:"
```

**Caddyfileを修正する必要がある場合**（`web:8000`を使用する場合）：

```bash
cat > Caddyfile << 'EOF'
toybox.ayatori-inc.co.jp {
	encode gzip

	# APIエンドポイント
	handle /api/* {
		reverse_proxy web:8000 {
			transport http {
				read_timeout 30s
				write_timeout 30s
			}
		}
	}

	# アップロードファイル
	handle /uploads/* {
		reverse_proxy web:8000 {
			transport http {
				read_timeout 60s
				write_timeout 60s
			}
		}
	}

	# ヘルスチェック
	handle /health {
		reverse_proxy web:8000
	}

	# その他のリクエストはwebサービスに転送
	reverse_proxy web:8000 {
		transport http {
			read_timeout 30s
			write_timeout 30s
		}
	}
}
EOF
```

### ステップ7: Dockerコンテナを起動

```bash
# プロジェクトディレクトリに移動
cd /home/app/toybox
# または
cd /root/toybox

# 既存のコンテナを停止
docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null
docker compose down 2>/dev/null

# backendディレクトリのコンテナを起動（webサービスなど）
cd backend
docker compose up -d --build

# ルートディレクトリに戻る
cd ..

# Caddyコンテナを起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker ps | grep -E 'caddy|web'
```

### ステップ8: Caddyのログを確認

```bash
# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# エラーがないか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i error
```

### ステップ9: 動作確認

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# ポート80/443がCaddyコンテナに割り当てられているか確認
docker ps | grep caddy
sudo netstat -tlnp | grep -E ':80|:443'
```

---

## 代替案: backend/docker-compose.ymlのnginxサービスを使用

Caddyが起動しない場合、一時的に`backend/docker-compose.yml`のnginxサービスを使用することもできます。

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

# nginxサービスが起動しているか確認
docker compose ps | grep nginx
```

**注意**: この方法は一時的な対応です。本番環境ではCaddyを使用することを推奨します。

---

## トラブルシューティング

### Caddyコンテナが起動しない場合

```bash
# Caddyのログを詳細に確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# Caddyfileの構文を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

### ポート80/443が既に使用されている場合

```bash
# ポート80/443を使用しているプロセスを確認
sudo lsof -i :80
sudo lsof -i :443

# プロセスを停止
sudo systemctl stop <サービス名>
# または
sudo kill -9 <PID>
```

### webサービスに接続できない場合

```bash
# webサービスが起動しているか確認
cd /home/app/toybox/backend
docker compose ps | grep web

# webサービスのログを確認
docker compose logs web --tail=50

# webサービスに直接接続テスト
docker compose exec web curl http://localhost:8000/api/health/
```

---

## 確認事項

修正後、以下を確認してください：

1. ✅ Caddyコンテナが起動している（`docker ps | grep caddy`）
2. ✅ ポート80/443がCaddyコンテナに割り当てられている（`docker ps | grep caddy`）
3. ✅ ポート80/443でアクセスできる（`curl http://toybox.ayatori-inc.co.jp`）
4. ✅ webサービスが起動している（`docker compose ps | grep web`）
