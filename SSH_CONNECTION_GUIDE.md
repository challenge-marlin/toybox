# SSH接続ガイド

## 現在の状況
`app@160.251.168.144` への接続で「Permission denied」エラーが発生しています。

## 解決方法

### 方法1: rootユーザーで接続（推奨）

まず、`root`ユーザーで接続を試してください：

```bash
ssh root@160.251.168.144
```

接続が成功したら、以下の手順で`app`ユーザーを作成・設定します：

```bash
# 1. appユーザーを作成
adduser app
# パスワードを設定（セキュリティのため、強力なパスワードを設定）

# 2. appユーザーをsudoグループに追加
usermod -aG sudo app

# 3. appユーザーのホームディレクトリに.sshディレクトリを作成
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh

# 4. SSH公開鍵を設定（ローカルマシンから公開鍵をコピー）
# ローカルマシンで以下を実行：
# ssh-copy-id app@160.251.168.144
# または、手動で公開鍵をコピー：
# cat ~/.ssh/id_rsa.pub | ssh root@160.251.168.144 "cat >> /home/app/.ssh/authorized_keys"

# 5. 権限を設定
chown -R app:app /home/app/.ssh
chmod 600 /home/app/.ssh/authorized_keys
```

### 方法2: パスワード認証で接続

もし`app`ユーザーが既に存在する場合は、パスワード認証を有効にする必要があるかもしれません：

```bash
# rootで接続後、SSH設定を確認
sudo nano /etc/ssh/sshd_config

# 以下の行を確認/修正：
# PasswordAuthentication yes
# PubkeyAuthentication yes

# SSHサービスを再起動
sudo systemctl restart sshd
```

### 方法3: 既存のSSHキーを使用

ローカルマシンにSSHキーがある場合は、明示的に指定：

```bash
# デフォルトのキーを使用
ssh -i ~/.ssh/id_rsa app@160.251.168.144

# または、別のキーを使用
ssh -i ~/.ssh/your_key app@160.251.168.144
```

## 確認手順

接続が成功したら、以下を確認：

```bash
# 現在のユーザーを確認
whoami

# ホームディレクトリを確認
pwd

# プロジェクトディレクトリに移動（存在する場合）
cd ~/toybox
```

## トラブルシューティング

### rootでも接続できない場合
1. サーバーのIPアドレスが正しいか確認
2. ファイアウォールでSSHポート（22）が開いているか確認
3. ConoHaの管理画面でSSH接続が許可されているか確認

### パスワードが分からない場合
1. ConoHaの管理画面でパスワードをリセット
2. または、VNC/コンソールから直接サーバーにアクセス

### SSHキーが正しく設定されていない場合
1. ローカルマシンでSSHキーを生成：
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```
2. 公開鍵をサーバーにコピー：
   ```bash
   ssh-copy-id app@160.251.168.144
   ```

