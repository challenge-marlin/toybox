# 502 Bad Gateway エラー解決手順

## 問題
`https://toybox.ayatori-inc.co.jp/`にアクセスすると「502 Bad Gateway」エラーが発生。

## 原因の可能性
1. **webサービスが起動していない**
2. **Caddyとwebサービスが異なるDockerネットワークに接続されている**
3. **webサービスがクラッシュしている**
4. **Caddyfileの設定が間違っている（サービス名やポート番号）**

## 緊急診断コマンド（サーバー側で実行）

### ステップ1: webサービスが起動しているか確認

```bash
cd /var/www/toybox/backend

# webサービスが起動しているか確認
docker compose ps

# webサービスがUp状態か確認
docker compose ps | grep web

# webサービスのログを確認（最新50行）
docker compose logs web --tail=50

# エラーがないか確認
docker compose logs web | grep -i "error\|exception\|failed"
```

**確認ポイント**:
- webサービスが`Up`状態か
- エラーログがないか

### ステップ2: webサービスに直接接続できるか確認

```bash
cd /var/www/toybox/backend

# webサービスコンテナ内からヘルスチェック
docker compose exec web curl http://localhost:8000/api/health/

# または、ホストから直接接続（ポート8000が公開されている場合）
curl http://localhost:8000/api/health/
```

**確認ポイント**:
- webサービスが正常に応答するか

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

### ステップ4: Caddyからwebサービスに接続できるか確認

```bash
cd /var/www/toybox

# Caddyコンテナ内からwebサービスに接続テスト
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy curl http://web:8000/api/health/

# または、wgetを使用
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy wget -O- http://web:8000/api/health/
```

**確認ポイント**:
- Caddyコンテナからwebサービスに接続できるか
- 接続できない場合、ネットワーク設定の問題の可能性が高い

### ステップ5: Caddyfileの設定を確認

```bash
cd /var/www/toybox

# Caddyfileの内容を確認
cat Caddyfile

# webサービス名とポート番号が正しいか確認
# backend/docker-compose.ymlのサービス名を確認
cat backend/docker-compose.yml | grep -A 5 "web:"
```

**確認ポイント**:
- Caddyfileで`web:8000`を参照しているか
- サービス名とポート番号が正しいか

### ステップ6: Caddyのログを確認

```bash
cd /var/www/toybox

# Caddyのログを確認（最新100行）
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=100

# エラーがないか確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy | grep -i "error\|502\|bad gateway"
```

**確認ポイント**:
- Caddyがwebサービスに接続しようとしているか
- エラーメッセージがないか

---

## 解決手順

### 方法A: webサービスが起動していない場合

```bash
cd /var/www/toybox/backend

# webサービスを起動
docker compose up -d --build

# 状態を確認
docker compose ps

# webサービスが起動するまで待つ（30秒程度）
sleep 30

# 再度確認
docker compose ps | grep web

# webサービスのログを確認
docker compose logs web --tail=50
```

### 方法B: Caddyとwebサービスが異なるネットワークに接続されている場合

**問題**: `docker network inspect backend_default`でCaddyとwebサービスが表示されない場合。

**解決策1**: `docker-compose.prod.yml`でネットワーク設定を確認

```bash
cd /var/www/toybox

# docker-compose.prod.ymlの内容を確認
cat docker-compose.prod.yml

# backend_defaultネットワークが存在するか確認
docker network ls | grep backend

# ネットワークが存在しない場合、backendディレクトリのコンテナを起動して作成
cd /var/www/toybox/backend
docker compose up -d
cd ..
```

**解決策2**: Caddyコンテナを再作成

```bash
cd /var/www/toybox

# Caddyコンテナを停止
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop caddy

# Caddyコンテナを削除
docker compose -f docker-compose.yml -f docker-compose.prod.yml rm -f caddy

# Caddyコンテナを再作成
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build caddy

# ネットワークを確認
docker network inspect backend_default | grep -E "caddy|web"
```

### 方法C: Caddyfileの設定を修正

**問題**: Caddyfileで`frontend:3000`や`backend:4000`を参照している場合。

**解決策**: Caddyfileを`web:8000`を参照するように修正

```bash
cd /var/www/toybox

# Caddyfileをバックアップ
cp Caddyfile Caddyfile.backup

# Caddyfileを修正
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

# Caddyfileが正しく作成されたか確認
cat Caddyfile

# Caddyコンテナを再起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart caddy

# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=50
```

### 方法D: webサービスがクラッシュしている場合

```bash
cd /var/www/toybox/backend

# webサービスのログを詳細に確認
docker compose logs web

# webサービスを再起動
docker compose restart web

# または、再作成
docker compose up -d --force-recreate web

# webサービスのログを確認
docker compose logs web --tail=50
```

---

## 確認チェックリスト

以下の項目を順番に確認してください：

1. [ ] webサービスが`Up`状態で起動している
2. [ ] webサービスがポート8000でリッスンしている
3. [ ] webサービスに直接接続できる（`curl http://localhost:8000/api/health/`）
4. [ ] Caddyとwebサービスが同じネットワーク（`backend_default`）に接続されている
5. [ ] Caddyからwebサービスに接続できる（`docker exec caddy curl http://web:8000/api/health/`）
6. [ ] Caddyfileで`web:8000`を参照している
7. [ ] Caddyのログにエラーがない

---

## トラブルシューティング

### webサービスが起動しない場合

```bash
cd /var/www/toybox/backend

# webサービスのログを確認
docker compose logs web

# データベース接続エラーの場合
docker compose exec web python manage.py check
docker compose exec web python manage.py migrate

# 環境変数の確認
docker compose exec web env | grep -E "DB_|REDIS_"
```

### Caddyからwebサービスに接続できない場合

```bash
# ネットワークを確認
docker network inspect backend_default

# Caddyコンテナのネットワーク設定を確認
docker inspect $(docker ps -q --filter "ancestor=caddy") | grep -A 20 "Networks"

# webサービスのネットワーク設定を確認
cd /var/www/toybox/backend
docker inspect $(docker compose ps -q web) | grep -A 20 "Networks"
```

---

## 次のステップ

すべての確認が完了したら：

1. **ブラウザでアクセス**: `https://toybox.ayatori-inc.co.jp`
2. **SSO処理をテスト**: SSOログインを試行して、502エラーが発生しないか確認
3. **ログを監視**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy`でリアルタイムログを確認
