#!/bin/bash
# 手動デプロイスクリプト
# 使用方法: ./scripts/deploy.sh

set -e

# 設定
VPS_HOST="${VPS_HOST:-160.251.168.144}"
VPS_USER="${VPS_USER:-app}"
SSH_KEY="${SSH_KEY:-~/.ssh/id_rsa}"

echo "=== ToyBox デプロイスクリプト ==="
echo "Host: $VPS_HOST"
echo "User: $VPS_USER"
echo ""

# SSH接続テスト
echo "1. SSH接続をテスト中..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 "$VPS_USER@$VPS_HOST" "echo 'SSH接続成功'" 2>/dev/null; then
    echo "❌ SSH接続に失敗しました"
    echo "以下を確認してください:"
    echo "  - SSH鍵が正しく設定されているか"
    echo "  - VPS_HOSTとVPS_USERが正しいか"
    echo "  - サーバーが稼働しているか"
    exit 1
fi
echo "✅ SSH接続成功"
echo ""

# デプロイ実行
echo "2. デプロイを実行中..."
ssh -i "$SSH_KEY" "$VPS_USER@$VPS_HOST" << 'DEPLOY_SCRIPT'
set -e

# プロジェクトディレクトリに移動
cd ~/toybox || cd /home/app/toybox || {
    echo "❌ プロジェクトディレクトリが見つかりません"
    exit 1
}

echo "現在のディレクトリ: $(pwd)"

# Gitの状態を確認
if [ ! -d .git ]; then
    echo "❌ Gitリポジトリが見つかりません"
    exit 1
fi

# 最新のコードを取得
echo "最新のコードを取得中..."
git fetch origin main
git reset --hard origin/main
git clean -fd

# 環境変数ファイルの確認
if [ ! -f backend/.env ]; then
    echo "⚠️  Warning: backend/.env not found"
    echo "環境変数ファイルを作成してください"
fi

# Docker Composeで再ビルド・再起動
echo "コンテナを停止中..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down || true

echo "コンテナをビルド・起動中..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
echo "コンテナの状態を確認中..."
sleep 10
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# ヘルスチェック
echo "ヘルスチェックを実行中..."
sleep 5
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ ヘルスチェック成功"
else
    echo "⚠️  ヘルスチェック失敗（コンテナが起動中かもしれません）"
fi

echo ""
echo "✅ デプロイ完了！"
DEPLOY_SCRIPT

echo ""
echo "=== デプロイ完了 ==="

