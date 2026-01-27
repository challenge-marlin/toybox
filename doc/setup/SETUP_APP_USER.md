# appユーザーのセットアップ手順

## 現在の状況
- `root`ユーザーでサーバーに接続できている
- `app`ユーザーが存在しない

## 手順

### 方法1: スクリプトを使用（推奨）

サーバー上で以下のコマンドを実行：

```bash
# スクリプトをダウンロード（または手動で作成）
# ローカルマシンからスクリプトをアップロード
scp setup-app-user.sh root@160.251.168.144:/root/

# サーバーで実行
ssh root@160.251.168.144
chmod +x /root/setup-app-user.sh
/root/setup-app-user.sh
```

### 方法2: 手動で実行

サーバー上で以下のコマンドを順番に実行：

```bash
# 1. appユーザーを作成
adduser app
# パスワードを設定してください（セキュリティのため、強力なパスワードを推奨）

# 2. appユーザーをsudoグループに追加
usermod -aG sudo app

# 3. SSHディレクトリを作成
mkdir -p /home/app/.ssh
chmod 700 /home/app/.ssh
chown app:app /home/app/.ssh

# 4. authorized_keysファイルを作成
touch /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys

# 5. プロジェクトディレクトリを作成
mkdir -p /home/app/toybox
chown app:app /home/app/toybox
```

## SSH公開鍵の設定

### ローカルマシンにSSHキーがある場合

ローカルマシンで以下を実行：

```bash
# SSH公開鍵をサーバーにコピー
ssh-copy-id app@160.251.168.144
```

または、手動でコピー：

```bash
# ローカルマシンで公開鍵を表示
cat ~/.ssh/id_rsa.pub

# サーバーで（rootユーザーとして）公開鍵を追加
ssh root@160.251.168.144
echo "ここにローカルで表示された公開鍵を貼り付け" >> /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
```

### SSHキーが存在しない場合

ローカルマシンでSSHキーを生成：

```bash
# SSHキーを生成
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
# パスフレーズを設定（推奨）またはEnterでスキップ

# 生成した公開鍵をサーバーにコピー
ssh-copy-id app@160.251.168.144
```

## 接続テスト

```bash
# appユーザーで接続をテスト
ssh app@160.251.168.144

# 接続が成功したら、以下を確認
whoami  # app と表示されるはず
pwd     # /home/app と表示されるはず
```

## 次にやること

1. ✅ appユーザーを作成
2. ✅ SSH公開鍵を設定
3. ✅ appユーザーで接続できることを確認
4. ⏭️ プロジェクトをクローン/セットアップ
5. ⏭️ nginxを停止してCaddyを起動

