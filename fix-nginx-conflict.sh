#!/bin/bash
# nginx競合問題を解決し、Caddyを起動するスクリプト

set -e

echo "=== nginx競合問題の解決スクリプト ==="
echo ""

# 1. nginxの状態を確認
echo "1. nginxの状態を確認中..."
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "   [警告] システムレベルのnginxが実行中です"
    echo "   nginxを停止しますか？ (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "   nginxを停止中..."
        sudo systemctl stop nginx
        sudo systemctl disable nginx
        echo "   [OK] nginxを停止しました"
    else
        echo "   [スキップ] nginxの停止をスキップしました"
    fi
else
    echo "   [OK] システムレベルのnginxは実行されていません"
fi

# 2. Dockerコンテナのnginxを確認
echo ""
echo "2. Dockerコンテナのnginxを確認中..."
nginx_containers=$(docker ps -q --filter "ancestor=nginx" 2>/dev/null || true)
if [ -n "$nginx_containers" ]; then
    echo "   [警告] nginxコンテナが実行中です"
    echo "   nginxコンテナを停止しますか？ (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "   nginxコンテナを停止中..."
        docker stop $nginx_containers
        docker rm $nginx_containers
        echo "   [OK] nginxコンテナを停止しました"
    else
        echo "   [スキップ] nginxコンテナの停止をスキップしました"
    fi
else
    echo "   [OK] nginxコンテナは実行されていません"
fi

# 3. ポート80/443の使用状況を確認
echo ""
echo "3. ポート80/443の使用状況を確認中..."
if command -v lsof >/dev/null 2>&1; then
    port80=$(sudo lsof -i :80 2>/dev/null | grep -v "COMMAND" || true)
    port443=$(sudo lsof -i :443 2>/dev/null | grep -v "COMMAND" || true)
    
    if [ -n "$port80" ]; then
        echo "   [警告] ポート80が使用中です:"
        echo "$port80"
    else
        echo "   [OK] ポート80は使用されていません"
    fi
    
    if [ -n "$port443" ]; then
        echo "   [警告] ポート443が使用中です:"
        echo "$port443"
    else
        echo "   [OK] ポート443は使用されていません"
    fi
elif command -v netstat >/dev/null 2>&1; then
    port80=$(sudo netstat -tlnp | grep :80 || true)
    port443=$(sudo netstat -tlnp | grep :443 || true)
    
    if [ -n "$port80" ]; then
        echo "   [警告] ポート80が使用中です:"
        echo "$port80"
    else
        echo "   [OK] ポート80は使用されていません"
    fi
    
    if [ -n "$port443" ]; then
        echo "   [警告] ポート443が使用中です:"
        echo "$port443"
    else
        echo "   [OK] ポート443は使用されていません"
    fi
else
    echo "   [スキップ] lsof/netstatが見つかりません"
fi

# 4. Caddyfileの構文を確認
echo ""
echo "4. Caddyfileの構文を確認中..."
if [ -f "Caddyfile" ]; then
    if docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T caddy caddy validate --config /etc/caddy/Caddyfile 2>/dev/null; then
        echo "   [OK] Caddyfileの構文は正しいです"
    else
        echo "   [警告] Caddyfileの構文に問題がある可能性があります"
        echo "   Caddyコンテナが起動していない場合は、このチェックはスキップされます"
    fi
else
    echo "   [エラー] Caddyfileが見つかりません"
    exit 1
fi

# 5. Caddyコンテナを再起動
echo ""
echo "5. Caddyコンテナを再起動中..."
cd "$(dirname "$0")"
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 6. サービスの状態を確認
echo ""
echo "6. サービスの状態を確認中..."
sleep 5
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 7. Caddyのログを表示
echo ""
echo "7. Caddyのログ（最新20行）:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=20 caddy

echo ""
echo "=== 完了 ==="
echo ""
echo "次のステップ:"
echo "1. ブラウザで https://toybox.ayatori-inc.co.jp にアクセスして確認"
echo "2. エラーが続く場合は、以下を確認してください:"
echo "   - docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy"
echo "   - sudo lsof -i :80"
echo "   - sudo lsof -i :443"

