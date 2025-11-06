# appユーザーセットアップ手順（詳細版）

## ⚠️ 重要な注意事項

**これらのコマンドは、Windows PowerShellではなく、Linuxサーバー上で実行する必要があります。**

まず、SSHでサーバーに接続してから、そのサーバー上でコマンドを実行してください。

## 手順

### ステップ1: サーバーにSSH接続

**Windows PowerShellで実行：**

```powershell
ssh root@160.251.168.144
```

パスワードを入力すると、サーバーのターミナル（`[root@... ~]#`のようなプロンプト）が表示されます。

### ステップ2: サーバー上でコマンドを実行

**サーバーのターミナルで実行（rootユーザーとして）：**

```bash
# 1. appユーザーを作成
adduser app
# パスワードを設定してください（強力なパスワードを推奨）

# 2. sudoパッケージをインストール
yum install -y sudo
# または（新しいバージョンの場合）
dnf install -y sudo

# 3. wheelグループを作成（存在しない場合）
groupadd wheel

# 4. appユーザーをwheelグループに追加
usermod -aG wheel app

# 5. sudo設定を確認・追加
echo "%wheel  ALL=(ALL)       ALL" >> /etc/sudoers

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

### ステップ3: SSH公開鍵を設定

**Windows PowerShellに戻って実行：**

```powershell
# SSH公開鍵をサーバーにコピー
ssh-copy-id app@160.251.168.144
```

SSHキーがない場合は、まず生成：

```powershell
# SSHキーを生成
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### ステップ4: appユーザーで接続テスト

```powershell
ssh app@160.251.168.144
```

## 違いの説明

- **Windows PowerShell**: あなたのローカルマシン（Windows）
- **Linuxサーバー**: リモートサーバー（160.251.168.144）

コマンドは、**Linuxサーバーに接続した後**に実行する必要があります。

## 視覚的な説明

```
Windows PowerShell
    ↓ ssh root@160.251.168.144
    ↓
Linuxサーバー（rootユーザー）
    ↓ ここでコマンドを実行
    ↓ adduser app
    ↓ yum install -y sudo
    ↓ ...
    ↓ exit（またはCtrl+D）
    ↓
Windows PowerShellに戻る
    ↓ ssh-copy-id app@160.251.168.144
    ↓
    ↓ ssh app@160.251.168.144
    ↓
Linuxサーバー（appユーザー）✅
```

