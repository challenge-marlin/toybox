#!/bin/bash
# appユーザーのセットアップスクリプト
# rootユーザーで実行してください

set -e

echo "=== appユーザーのセットアップ ==="
echo ""

# 1. appユーザーを作成
echo "1. appユーザーを作成中..."
if id "app" &>/dev/null; then
    echo "   [情報] appユーザーは既に存在します"
else
    adduser app
    echo "   [OK] appユーザーを作成しました"
fi

# 2. sudoグループに追加
echo ""
echo "2. appユーザーをsudoグループに追加中..."
usermod -aG sudo app
echo "   [OK] appユーザーをsudoグループに追加しました"

# 3. SSHディレクトリを作成
echo ""
echo "3. SSHディレクトリを作成中..."
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh
chown app:app /home/app/.ssh
echo "   [OK] SSHディレクトリを作成しました"

# 4. authorized_keysファイルを作成（存在しない場合）
echo ""
echo "4. authorized_keysファイルを準備中..."
touch /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys
echo "   [OK] authorized_keysファイルを準備しました"

# 5. プロジェクトディレクトリを作成
echo ""
echo "5. プロジェクトディレクトリを作成中..."
mkdir -p /home/app/toybox
chown app:app /home/app/toybox
echo "   [OK] プロジェクトディレクトリを作成しました"

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. ローカルマシンからSSH公開鍵をコピー:"
echo "   ssh-copy-id app@160.251.168.144"
echo ""
echo "2. または、手動で公開鍵を追加:"
echo "   cat ~/.ssh/id_rsa.pub | ssh root@160.251.168.144 'cat >> /home/app/.ssh/authorized_keys'"
echo ""
echo "3. appユーザーで接続をテスト:"
echo "   ssh app@160.251.168.144"

