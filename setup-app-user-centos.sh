#!/bin/bash
# appユーザーのセットアップスクリプト（CentOS/RHEL系対応）
# rootユーザーで実行してください

set -e

echo "=== appユーザーのセットアップ（CentOS/RHEL系） ==="
echo ""

# ディストリビューションを確認
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "ディストリビューション: $ID $VERSION_ID"
fi

# 1. appユーザーを作成
echo "1. appユーザーを作成中..."
if id "app" &>/dev/null; then
    echo "   [情報] appユーザーは既に存在します"
else
    adduser app
    echo "   [OK] appユーザーを作成しました"
    echo "   パスワードを設定してください:"
    passwd app
fi

# 2. sudoパッケージをインストール
echo ""
echo "2. sudoパッケージを確認中..."
if command -v yum >/dev/null 2>&1; then
    yum install -y sudo || true
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y sudo || true
elif command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get install -y sudo || true
fi

# 3. wheelグループを作成（存在しない場合）
echo ""
echo "3. wheelグループを確認中..."
if ! getent group wheel >/dev/null 2>&1; then
    groupadd wheel
    echo "   [OK] wheelグループを作成しました"
else
    echo "   [情報] wheelグループは既に存在します"
fi

# 4. appユーザーをwheelグループに追加
echo ""
echo "4. appユーザーをwheelグループに追加中..."
usermod -aG wheel app
echo "   [OK] appユーザーをwheelグループに追加しました"

# 5. sudo設定を確認
echo ""
echo "5. sudo設定を確認中..."
if ! grep -q "^%wheel" /etc/sudoers 2>/dev/null; then
    echo "   [警告] wheelグループのsudo設定が見つかりません"
    echo "   visudoを実行して、以下の行を有効化してください:"
    echo "   %wheel  ALL=(ALL)       ALL"
    echo ""
    echo "   自動的に追加しますか？ (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "%wheel  ALL=(ALL)       ALL" >> /etc/sudoers
        echo "   [OK] sudo設定を追加しました"
    fi
else
    echo "   [OK] sudo設定は正しく設定されています"
fi

# 6. SSHディレクトリを作成
echo ""
echo "6. SSHディレクトリを作成中..."
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh
chown app:app /home/app/.ssh
echo "   [OK] SSHディレクトリを作成しました"

# 7. authorized_keysファイルを作成
echo ""
echo "7. authorized_keysファイルを準備中..."
touch /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys
echo "   [OK] authorized_keysファイルを準備しました"

# 8. プロジェクトディレクトリを作成
echo ""
echo "8. プロジェクトディレクトリを作成中..."
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
echo "2. appユーザーで接続をテスト:"
echo "   ssh app@160.251.168.144"
echo ""
echo "3. sudo権限をテスト:"
echo "   sudo whoami"

