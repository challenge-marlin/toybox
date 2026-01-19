#!/bin/bash
# Caddyfileを元の設定に戻し、webサービスとCaddyを再起動するスクリプト

set -e

echo "=== Caddyfileを元の設定に戻します ==="

# プロジェクトディレクトリに移動
cd /var/www/toybox

# 現在のCaddyfileをバックアップ
if [ -f Caddyfile ]; then
    BACKUP_NAME="Caddyfile.backup.$(date +%Y%m%d_%H%M%S)"
    cp Caddyfile "$BACKUP_NAME"
    echo "✅ Caddyfileをバックアップしました: $BACKUP_NAME"
fi

# Caddyfileを元の設定に戻す
cat > Caddyfile << 'EOF'
toybox.ayatori-inc.co.jp {
	encode gzip

	# APIエンドポイント
	handle /api/* {
		reverse_proxy backend:4000 {
			header_up X-Forwarded-Proto {scheme}
			header_up X-Forwarded-For {remote_host}
			transport http {
				read_timeout 30s
				write_timeout 30s
			}
		}
	}

	# アップロードファイル
	handle /uploads/* {
		reverse_proxy backend:4000 {
			header_up X-Forwarded-Proto {scheme}
			header_up X-Forwarded-For {remote_host}
			transport http {
				read_timeout 60s
				write_timeout 60s
			}
		}
	}

	# ヘルスチェック
	handle /health {
		reverse_proxy backend:4000 {
			header_up X-Forwarded-Proto {scheme}
			header_up X-Forwarded-For {remote_host}
		}
	}

	# フロントエンド
	reverse_proxy frontend:3000 {
		header_up X-Forwarded-Proto {scheme}
		header_up X-Forwarded-For {remote_host}
		transport http {
			read_timeout 30s
			write_timeout 30s
		}
	}
}

:4000 {
	encode gzip
	reverse_proxy backend:4000 {
		header_up X-Forwarded-Proto {scheme}
		header_up X-Forwarded-For {remote_host}
		transport http {
			read_timeout 30s
			write_timeout 30s
		}
	}
}
EOF

echo "✅ Caddyfileを元の設定に戻しました"

# webサービスの状態を確認
echo ""
echo "=== webサービスの状態を確認します ==="
cd /var/www/toybox/backend
docker compose ps

# webサービスを起動
echo ""
echo "=== webサービスを起動します ==="
docker compose up -d web worker beat

# webサービスが起動するまで待つ
echo "webサービスが起動するまで15秒待機します..."
sleep 15

# webサービスの状態を再確認
echo ""
echo "=== webサービスの状態を再確認します ==="
docker compose ps | grep -E "web|worker|beat" || docker compose ps

# Caddyコンテナを再起動
echo ""
echo "=== Caddyコンテナを再起動します ==="
cd /var/www/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart caddy

# Caddyのログを確認
echo ""
echo "=== Caddyのログを確認します ==="
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy --tail=20

echo ""
echo "✅ 完了しました！"
