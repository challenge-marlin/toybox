# appユーザーのセットアップ手順（CentOS/RHEL系）

## 現在の状況
- `sudo`グループが存在しない（CentOS/RHEL系の可能性）
- 接続が閉じられた

## 解決方法

### 1. sudoパッケージをインストール（まだの場合）

```bash
# rootユーザーで接続
ssh root@160.251.168.144

# sudoパッケージをインストール
yum install -y sudo
# または（新しいバージョンの場合）
dnf install -y sudo
```

### 2. appユーザーをwheelグループに追加（CentOS/RHEL系）

CentOS/RHEL系では、`sudo`の代わりに`wheel`グループを使用します：

```bash
# appユーザーをwheelグループに追加
usermod -aG wheel app

# wheelグループが存在しない場合は、wheelグループを作成
groupadd wheel
usermod -aG wheel app
```

### 3. sudoの設定を確認

```bash
# sudoの設定ファイルを確認
visudo

# 以下の行がコメントアウトされていないか確認（コメントアウトされていたら有効化）
# %wheel  ALL=(ALL)       ALL
```

### 4. 完全なセットアップ手順

```bash
# rootユーザーで接続
ssh root@160.251.168.144

# 1. appユーザーを作成（まだの場合）
if ! id "app" &>/dev/null; then
    adduser app
    passwd app  # パスワードを設定
fi

# 2. sudoパッケージをインストール
yum install -y sudo || dnf install -y sudo

# 3. wheelグループを作成（存在しない場合）
groupadd wheel 2>/dev/null || true

# 4. appユーザーをwheelグループに追加
usermod -aG wheel app

# 5. sudo設定を確認
grep -q "^%wheel" /etc/sudoers || echo "%wheel  ALL=(ALL)       ALL" >> /etc/sudoers

# 6. SSHディレクトリを作成
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh
chown app:app /home/app/.ssh

# 7. authorized_keysファイルを作成
touch /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys

# 8. プロジェクトディレクトリを作成
mkdir -p /home/app/toybox
chown app:app /home/app/toybox
```

## ディストリビューションの確認

どのディストリビューションを使っているか確認：

```bash
cat /etc/os-release
```

- Ubuntu/Debian系: `sudo`グループを使用
- CentOS/RHEL系: `wheel`グループを使用
- その他: ディストリビューションに応じて設定

