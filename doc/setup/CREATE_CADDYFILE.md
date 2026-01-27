# Caddyfile作成手順

## 問題
`/var/www/toybox`にCaddyfileが存在しない。

## 解決手順

### ステップ1: backend/docker-compose.ymlのサービス名を確認

```bash
cd /var/www/toybox/backend
cat docker-compose.yml | grep -A 10 "services:"
cat docker-compose.yml | grep -A 5 "web:"
```

**確認ポイント**:
- サービス名が`web`かどうか
- ポート番号が`8000`かどうか

### ステップ2: Caddyfileを作成

`/var/www/toybox`ディレクトリでCaddyfileを作成：

```bash
cd /var/www/toybox

# Caddyfileを作成
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

### ステップ3: docker-compose.prod.ymlを作成（存在しない場合）

```bash
cd /var/www/toybox

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

# docker-compose.prod.ymlが作成されたか確認
ls -la docker-compose.prod.yml
cat docker-compose.prod.yml
```

**注意**: `depends_on: web`は、`backend/docker-compose.yml`の`web`サービスを参照しています。Caddyとwebサービスが同じDockerネットワークに接続されている必要があります。

### ステップ4: Dockerネットワークを確認

```bash
# backendディレクトリのコンテナが起動しているか確認
cd /var/www/toybox/backend
docker compose ps

# Dockerネットワークを確認
docker network ls
docker network inspect backend_default 2>/dev/null | grep -A 5 "web"
```

### ステップ5: backendディレクトリのコンテナを起動（まだ起動していない場合）

```bash
cd /var/www/toybox/backend

# コンテナを起動
docker compose up -d --build

# コンテナの状態を確認
docker compose ps

# webサービスが起動しているか確認
docker compose ps | grep web
```

### ステップ6: Caddyコンテナを起動

```bash
cd /var/www/toybox

# システムレベルのnginxを停止
sudo systemctl stop nginx
sudo systemctl disable nginx
sudo pkill -9 nginx

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

# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy

# エラーがないか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i error
```

### ステップ8: 動作確認

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

### Caddyコンテナがwebサービスに接続できない場合

**問題**: Caddyとwebサービスが異なるDockerネットワークに接続されている可能性があります。

**解決策**: `docker-compose.prod.yml`で、backendディレクトリのネットワークを指定する必要があります。

```bash
cd /var/www/toybox/backend

# ネットワーク名を確認
docker compose config | grep -A 5 "networks:"

# 通常は "backend_default" という名前です
```

その後、`docker-compose.prod.yml`を修正：

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
    networks:
      - backend_default  # backendディレクトリのネットワーク名

networks:
  backend_default:
    external: true  # 既存のネットワークを使用

volumes:
  caddy-data:
  caddy-config:
```

### Caddyfileの構文エラー

```bash
# Caddyfileの構文を確認
cd /var/www/toybox
docker run --rm -v $(pwd)/Caddyfile:/etc/caddy/Caddyfile:ro caddy:2 caddy validate --config /etc/caddy/Caddyfile
```

---

## 確認事項

作成後、以下を確認してください：

1. ✅ Caddyfileが存在する（`ls -la /var/www/toybox/Caddyfile`）
2. ✅ docker-compose.prod.ymlが存在する（`ls -la /var/www/toybox/docker-compose.prod.yml`）
3. ✅ webサービスが起動している（`cd /var/www/toybox/backend && docker compose ps | grep web`）
4. ✅ Caddyコンテナが起動している（`cd /var/www/toybox && docker ps | grep caddy`）
