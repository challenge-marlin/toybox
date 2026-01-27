# docker-compose.prod.yml作成手順

## 問題
`/var/www/toybox/docker-compose.prod.yml`が存在しない。

## 解決手順

### ステップ1: プロジェクトディレクトリに移動

```bash
cd /var/www/toybox

# 現在のディレクトリを確認
pwd
ls -la
```

### ステップ2: backendディレクトリのネットワーク名を確認

```bash
cd /var/www/toybox/backend

# ネットワーク名を確認
docker compose config | grep -A 5 "networks:"

# または、既存のネットワークを確認
docker network ls | grep backend
```

**通常は `backend_default` という名前です。**

### ステップ3: docker-compose.prod.ymlを作成

```bash
cd /var/www/toybox

# docker-compose.prod.ymlを作成
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
    networks:
      - backend_default

networks:
  backend_default:
    external: true

volumes:
  caddy-data:
  caddy-config:
EOF

# docker-compose.prod.ymlが作成されたか確認
ls -la docker-compose.prod.yml
cat docker-compose.prod.yml
```

### ステップ4: Caddyfileが存在するか確認

```bash
cd /var/www/toybox

# Caddyfileが存在するか確認
ls -la Caddyfile

# Caddyfileが存在しない場合、作成
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

	# SSOエンドポイント（タイムアウトを延長）
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

# Caddyfileが作成されたか確認
ls -la Caddyfile
cat Caddyfile
```

### ステップ5: backendディレクトリのコンテナが起動しているか確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps

# webサービスが起動していない場合、起動
docker compose up -d --build

# 状態を確認
docker compose ps | grep web
```

### ステップ6: Caddyコンテナを起動

```bash
cd /var/www/toybox

# システムレベルのnginxを停止（まだの場合）
sudo systemctl stop nginx 2>/dev/null
sudo systemctl disable nginx 2>/dev/null
sudo pkill -9 nginx 2>/dev/null

# ポート80/443が解放されているか確認
sudo netstat -tlnp | grep -E ':80|:443'

# Caddyコンテナを起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Caddyコンテナが起動しているか確認
docker ps | grep caddy
```

### ステップ7: Caddyのログを確認

```bash
cd /var/www/toybox

# Caddyのログを確認（最新50行）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=50

# エラーがないか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i error
```

### ステップ8: 動作確認

```bash
# ローカルからHTTPでテスト
curl -I http://toybox.ayatori-inc.co.jp

# ヘルスチェックエンドポイントをテスト
curl http://toybox.ayatori-inc.co.jp/health

# APIエンドポイントをテスト
curl http://toybox.ayatori-inc.co.jp/api/health/
```

---

## トラブルシューティング

### 問題1: backend_defaultネットワークが存在しない

```bash
# backendディレクトリのコンテナを起動してネットワークを作成
cd /var/www/toybox/backend
docker compose up -d

# ネットワークが作成されたか確認
docker network ls | grep backend
```

### 問題2: Caddyコンテナが起動しない

```bash
cd /var/www/toybox

# Caddyのログを詳細に確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# Caddyfileの構文を確認
docker run --rm -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2 caddy validate --config /etc/caddy/Caddyfile

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate caddy
```

### 問題3: Caddyからwebサービスに接続できない

```bash
# ネットワークを確認
docker network inspect backend_default | grep -E "caddy|web"

# Caddyコンテナ内からwebサービスに接続テスト
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl http://web:8000/api/health/
```

---

## 確認事項

作成後、以下を確認してください：

1. ✅ docker-compose.prod.ymlが存在する（`ls -la /var/www/toybox/docker-compose.prod.yml`）
2. ✅ Caddyfileが存在する（`ls -la /var/www/toybox/Caddyfile`）
3. ✅ webサービスが起動している（`cd /var/www/toybox/backend && docker compose ps | grep web`）
4. ✅ Caddyコンテナが起動している（`cd /var/www/toybox && docker ps | grep caddy`）
5. ✅ ポート80/443でアクセスできる（`curl http://toybox.ayatori-inc.co.jp`）
