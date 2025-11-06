#!/bin/bash
# SSH接続セットアップ完全自動化スクリプト
# サーバー側で rootユーザーとして実行してください

set -e

echo "=== SSH接続セットアップ完全自動化 ==="
echo ""

# 1. appユーザーの存在確認と作成
echo "1. appユーザーを確認中..."
if ! id "app" &>/dev/null; then
    echo "   appユーザーを作成します..."
    adduser app <<EOF
app_password_123
app_password_123
EOF
    echo "   [OK] appユーザーを作成しました"
else
    echo "   [情報] appユーザーは既に存在します"
fi

# 2. sudoパッケージの確認
echo ""
echo "2. sudoパッケージを確認中..."
if ! command -v sudo &>/dev/null; then
    if command -v yum &>/dev/null; then
        yum install -y sudo
    elif command -v dnf &>/dev/null; then
        dnf install -y sudo
    fi
    echo "   [OK] sudoパッケージをインストールしました"
else
    echo "   [情報] sudoパッケージは既にインストールされています"
fi

# 3. wheelグループの確認
echo ""
echo "3. wheelグループを確認中..."
if ! getent group wheel &>/dev/null; then
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

# 5. sudo設定の確認
echo ""
echo "5. sudo設定を確認中..."
if ! grep -q "^%wheel" /etc/sudoers 2>/dev/null; then
    echo "%wheel  ALL=(ALL)       ALL" >> /etc/sudoers
    echo "   [OK] sudo設定を追加しました"
else
    echo "   [情報] sudo設定は既に存在します"
fi

# 6. SSHディレクトリの作成
echo ""
echo "6. SSHディレクトリを作成中..."
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh
chown app:app /home/app/.ssh
echo "   [OK] SSHディレクトリを作成しました"

# 7. authorized_keysファイルの作成
echo ""
echo "7. authorized_keysファイルを準備中..."
touch /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys
echo "   [OK] authorized_keysファイルを準備しました"

# 8. パスワード認証を有効化
echo ""
echo "8. SSH設定を変更中（パスワード認証を有効化）..."
# バックアップを取る
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)

# PasswordAuthenticationを有効化
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# PubkeyAuthenticationを有効化
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# SSHサービスを再起動
systemctl restart sshd
echo "   [OK] SSH設定を変更し、サービスを再起動しました"

# 9. appユーザーのパスワードを設定（既存のパスワードを確認）
echo ""
echo "9. appユーザーのパスワードを設定中..."
echo "app_password_123" | passwd app --stdin
echo "   [OK] appユーザーのパスワードを設定しました"
echo "   パスワード: app_password_123"
echo "   ⚠️  セキュリティのため、接続後はパスワードを変更してください"

# 10. プロジェクトディレクトリの作成
echo ""
echo "10. プロジェクトディレクトリを作成中..."
mkdir -p /home/app/toybox
chown app:app /home/app/toybox
echo "   [OK] プロジェクトディレクトリを作成しました"

# 11. 権限の確認
echo ""
echo "11. 権限を確認中..."
ls -la /home/app/.ssh/
echo ""

echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. Windows PowerShellから以下で接続:"
echo "   ssh app@160.251.168.144"
echo "   パスワード: app_password_123"
echo ""
echo "2. 接続後、公開鍵を設定:"
echo "   Windows PowerShellで以下を実行:"
echo "   type \$env:USERPROFILE\\.ssh\\id_rsa.pub | ssh app@160.251.168.144 \"cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""
echo ""
echo "3. 公開鍵認証ができるようになったら、パスワード認証を無効化:"
echo "   vi /etc/ssh/sshd_config"
echo "   PasswordAuthentication no に変更"
echo "   systemctl restart sshd"

