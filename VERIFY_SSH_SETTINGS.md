# SSH設定の確認と修正手順

## 問題
WindowsからSSH接続してもPermission deniedエラーが出る

## 確認手順

### VNCコンソールで実行（rootユーザーで）

```bash
# 1. 現在のSSH設定を確認
grep -E "^PasswordAuthentication|^PubkeyAuthentication|^#PasswordAuthentication|^#PubkeyAuthentication" /etc/ssh/sshd_config

# 2. SSH設定ファイルを確認
cat /etc/ssh/sshd_config | grep -A 2 -B 2 PasswordAuthentication
cat /etc/ssh/sshd_config | grep -A 2 -B 2 PubkeyAuthentication
```

### 設定が正しくない場合の修正

```bash
# バックアップ
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup3

# パスワード認証を強制的に有効化
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 公開鍵認証を有効化
sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 設定が存在しない場合は追加
if ! grep -q "^PasswordAuthentication" /etc/ssh/sshd_config; then
    echo "" >> /etc/ssh/sshd_config
    echo "# Password authentication" >> /etc/ssh/sshd_config
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
fi

if ! grep -q "^PubkeyAuthentication" /etc/ssh/sshd_config; then
    echo "" >> /etc/ssh/sshd_config
    echo "# Public key authentication" >> /etc/ssh/sshd_config
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
fi

# 設定を確認
echo "=== 修正後の設定 ==="
grep -E "^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config

# SSH設定の構文チェック
sshd -t

# SSHサービスを再起動
systemctl restart sshd

# SSHサービスの状態を確認
systemctl status sshd

echo "完了！"
```

### 重要: SSHサービスが正しく再起動されているか確認

```bash
# SSHサービスの状態を確認
systemctl status sshd

# 実行中のプロセスを確認
ps aux | grep sshd

# ポート22がリッスンしているか確認
netstat -tlnp | grep :22
# または
ss -tlnp | grep :22
```

### ファイアウォールの確認

```bash
# ファイアウォールがSSHポートをブロックしていないか確認
firewall-cmd --list-all
# または
iptables -L -n | grep 22
```

### セルinuxの確認（もし有効な場合）

```bash
# SELinuxの状態を確認
getenforce

# もしEnforcingの場合、一時的に無効化（テスト用）
# setenforce 0
```

## Windows PowerShellから接続テスト

修正後、Windows PowerShellで：

```powershell
ssh root@160.251.168.144
```

パスワードを聞かれたら、rootユーザーのパスワードを入力してください。

