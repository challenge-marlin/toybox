# /var/www/toybox での作業手順

## プロジェクトディレクトリの場所
**`/var/www/toybox`** がプロジェクトのルートディレクトリです。

## 次のステップ

### ステップ1: プロジェクトディレクトリに移動

```bash
cd /var/www/toybox

# 現在のディレクトリを確認
pwd

# ファイル一覧を確認
ls -la
```

### ステップ2: 必要なファイルが存在するか確認

```bash
# Caddyfileが存在するか確認
ls -la Caddyfile
cat Caddyfile

# docker-compose.ymlが存在するか確認
ls -la docker-compose.yml
cat docker-compose.yml | head -20

# docker-compose.prod.ymlが存在するか確認
ls -la docker-compose.prod.yml

# backendディレクトリが存在するか確認
ls -la backend/
```

### ステップ3: Dockerコンテナの状態を確認

```bash
# すべてのDockerコンテナを確認
docker ps -a

# Caddyコンテナがあるか確認
docker ps -a | grep caddy

# backendディレクトリのコンテナを確認
cd backend
docker compose ps
cd ..
```

### ステップ4: システムレベルのnginxを停止

```bash
# nginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo pkill -9 nginx

# ポート80/443が解放されているか確認
sudo netstat -tlnp | grep -E ':80|:443'
```

### ステップ5: docker-compose.prod.ymlが存在しない場合、作成

```bash
# docker-compose.prod.ymlが存在するか確認
ls -la docker-compose.prod.yml

# 存在しない場合、作成
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

**注意**: Caddyfileが`frontend:3000`と`backend:4000`を参照している場合、実際のサービス名（`web:8000`など）に合わせてCaddyfileを修正する必要があるかもしれません。

### ステップ6: Caddyfileを確認・修正（必要に応じて）

```bash
# Caddyfileの内容を確認
cat Caddyfile

# backend/docker-compose.ymlのサービス名を確認
cat backend/docker-compose.yml | grep -A 5 "web:"
```

**Caddyfileが`frontend:3000`や`backend:4000`を参照している場合**、実際のサービス名（`web:8000`）に合わせて修正する必要があります：

```bash
# Caddyfileをバックアップ
cp Caddyfile Caddyfile.backup

# Caddyfileを修正（web:8000を使用する場合）
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

	# SSOエンドポイント
	handle /sso/* {
		reverse_proxy web:8000 {
			transport http {
				read_timeout 90s
				write_timeout 90s
			}
		}
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

### ステップ7: backendディレクトリのコンテナを起動

```bash
# backendディレクトリに移動
cd /var/www/toybox/backend

# Dockerコンテナを起動
docker compose up -d --build

# コンテナの状態を確認
docker compose ps

# webサービスが起動しているか確認
docker compose ps | grep web
```

### ステップ8: ルートディレクトリに戻ってCaddyコンテナを起動

```bash
# ルートディレクトリに戻る
cd /var/www/toybox

# 既存のコンテナを停止（既存のCaddyコンテナがある場合）
docker compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null

# Caddyコンテナを起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Caddyコンテナが起動しているか確認
docker ps | grep caddy
```

### ステップ9: Caddyのログを確認

```bash
# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# エラーがないか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i error
```

### ステップ10: 動作確認

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# ポート80/443がCaddyコンテナに割り当てられているか確認
docker ps | grep caddy
sudo netstat -tlnp | grep -E ':80|:443'
```

---

## トラブルシューティング

### Caddyコンテナが起動しない場合

```bash
# Caddyのログを詳細に確認
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# Caddyfileの構文を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

### webサービスに接続できない場合

```bash
# webサービスが起動しているか確認
cd /var/www/toybox/backend
docker compose ps | grep web

# webサービスのログを確認
docker compose logs web --tail=50

# webサービスに直接接続テスト
docker compose exec web curl http://localhost:8000/api/health/
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

---

## 確認事項

修正後、以下を確認してください：

1. ✅ webサービスが起動している（`cd /var/www/toybox/backend && docker compose ps | grep web`）
2. ✅ Caddyコンテナが起動している（`cd /var/www/toybox && docker ps | grep caddy`）
3. ✅ ポート80/443がCaddyコンテナに割り当てられている（`docker ps | grep caddy`）
4. ✅ ポート80/443でアクセスできる（`curl http://toybox.ayatori-inc.co.jp`）
