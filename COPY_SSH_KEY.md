# SSH公開鍵を手動で追加する手順

## 問題
Windows側とサーバー側のSSHキーが一致していないため、接続できない。

## 解決方法

### ステップ1: Windows PowerShellで公開鍵を表示

Windows PowerShellで以下を実行：

```powershell
# 公開鍵を表示
type $env:USERPROFILE\.ssh\id_rsa.pub

# または、存在しない場合は
cat ~/.ssh/id_rsa.pub
```

表示された内容（`ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ...`のような長い文字列）をコピーしてください。

### ステップ2: サーバー側で公開鍵を追加

サーバーに`root`ユーザーで接続：

```bash
ssh root@160.251.168.144
```

サーバー側で以下を実行：

```bash
# viエディタでauthorized_keysを編集
vi /home/app/.ssh/authorized_keys
```

または、直接追加：

```bash
# 以下のコマンドを実行後、Windowsでコピーした公開鍵を貼り付け
echo "ここにWindowsでコピーした公開鍵を貼り付け" >> /home/app/.ssh/authorized_keys

# 権限を設定
chown app:app /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chmod 700 /home/app/.ssh
```

### ステップ3: 接続テスト

Windows PowerShellに戻って：

```powershell
ssh app@160.251.168.144
```

## 代替方法：パスワード認証を一時的に有効化

SSH公開鍵の設定が難しい場合は、パスワード認証を一時的に有効にします：

### サーバー側（rootユーザー）で実行：

```bash
# SSH設定を編集
vi /etc/ssh/sshd_config

# 以下の行を見つけて変更：
# PasswordAuthentication yes
# PubkeyAuthentication yes

# 保存して終了（viの場合: Escキー → :wq → Enter）

# SSHサービスを再起動
systemctl restart sshd
```

### Windows PowerShellで接続：

```powershell
ssh app@160.251.168.144
# パスワードを入力（appユーザーのパスワード）
```

接続後、公開鍵を設定：

```bash
# サーバー側で（appユーザーとして）
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Windows PowerShellで公開鍵をコピー
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh app@160.251.168.144 "cat >> ~/.ssh/authorized_keys"
```

その後、パスワード認証を無効化（セキュリティのため）：

```bash
# サーバー側（rootユーザー）で
vi /etc/ssh/sshd_config
# PasswordAuthentication no に変更
systemctl restart sshd
```

