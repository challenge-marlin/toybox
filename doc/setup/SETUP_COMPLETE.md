# 完全自動セットアップ手順

## ステップ1: サーバー側でスクリプトを実行

サーバーに`root`ユーザーで接続：

```bash
ssh root@160.251.168.144
```

サーバー側で、以下のコマンドを順番に実行してください：

```bash
# 1. スクリプトを作成
cat > /root/setup-ssh-complete.sh << 'SCRIPT_END'
#!/bin/bash
set -e

echo "=== SSH接続セットアップ完全自動化 ==="

# appユーザーの確認と作成
if ! id "app" &>/dev/null; then
    adduser app
    echo "app_password_123" | passwd app --stdin
fi

# sudoパッケージの確認
if ! command -v sudo &>/dev/null; then
    yum install -y sudo || dnf install -y sudo
fi

# wheelグループの確認
if ! getent group wheel &>/dev/null; then
    groupadd wheel
fi

# appユーザーをwheelグループに追加
usermod -aG wheel app

# sudo設定
if ! grep -q "^%wheel" /etc/ssh/sudoers 2>/dev/null; then
    echo "%wheel  ALL=(ALL)       ALL" >> /etc/sudoers
fi

# SSHディレクトリ作成
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh
chown app:app /home/app/.ssh
touch /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys

# パスワード認証を有効化
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# プロジェクトディレクトリ作成
mkdir -p /home/app/toybox
chown app:app /home/app/toybox

echo "完了！パスワード: app_password_123"
SCRIPT_END

# 2. スクリプトを実行可能にする
chmod +x /root/setup-ssh-complete.sh

# 3. スクリプトを実行
/root/setup-ssh-complete.sh
```

## ステップ2: Windows PowerShellから接続

Windows PowerShellで以下を実行：

```powershell
ssh app@160.251.168.144
```

パスワードを聞かれたら、`app_password_123` を入力してください。

## ステップ3: 公開鍵を設定

接続できたら、Windows PowerShell（別のウィンドウ）で以下を実行：

```powershell
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh app@160.251.168.144 "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

パスワード `app_password_123` を入力してください。

## ステップ4: 接続テスト

公開鍵を設定した後、再度接続：

```powershell
ssh app@160.251.168.144
```

今度はパスワードなしで接続できるはずです。

## ステップ5: セキュリティ強化（推奨）

接続できたら、サーバー側でパスワード認証を無効化：

```bash
# サーバー側（appユーザーまたはrootユーザー）で
sudo vi /etc/ssh/sshd_config

# PasswordAuthentication no に変更
# 保存して終了

sudo systemctl restart sshd
```

これで完了です！

