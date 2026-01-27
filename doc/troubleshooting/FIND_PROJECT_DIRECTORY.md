# プロジェクトディレクトリの場所を探す手順

## 問題
`cd /home/app/toybox`を実行したが、「No such file or directory」エラーが発生。

## 解決手順

### ステップ1: プロジェクトディレクトリを探す

以下のコマンドを順番に実行して、プロジェクトディレクトリの場所を特定してください：

```bash
# 1. Caddyfileを探す（最も確実な方法）
find / -name "Caddyfile" -type f 2>/dev/null

# 2. docker-compose.ymlを探す
find / -name "docker-compose.yml" -type f 2>/dev/null | grep -v node_modules

# 3. toyboxという名前のディレクトリを探す
find / -type d -name "toybox" 2>/dev/null

# 4. 一般的な場所を確認
ls -la /home/
ls -la /home/app/
ls -la /root/
ls -la /opt/
ls -la /var/www/

# 5. 現在のユーザーのホームディレクトリを確認
pwd
whoami
echo $HOME
ls -la ~
```

### ステップ2: 見つかったディレクトリに移動

上記のコマンドで見つかったディレクトリに移動してください：

```bash
# 例: /root/toybox が見つかった場合
cd /root/toybox

# または、/opt/toybox が見つかった場合
cd /opt/toybox

# 現在のディレクトリを確認
pwd

# ファイル一覧を確認
ls -la
```

### ステップ3: 必要なファイルが存在するか確認

```bash
# Caddyfileが存在するか確認
ls -la Caddyfile

# docker-compose.ymlが存在するか確認
ls -la docker-compose.yml

# backendディレクトリが存在するか確認
ls -la backend/
```

### ステップ4: プロジェクトディレクトリが見つからない場合

プロジェクトディレクトリが見つからない場合は、以下のいずれかの可能性があります：

1. **プロジェクトがまだデプロイされていない**
   - Gitリポジトリからクローンする必要があります
   - または、WinSCPでファイルをアップロードする必要があります

2. **別の場所にデプロイされている**
   - サーバーの管理者に確認してください
   - または、`/var/www/`、`/opt/`、`/srv/`などの一般的な場所を確認してください

3. **別のユーザーでデプロイされている**
   - `sudo find /home -name "Caddyfile" 2>/dev/null`で全ユーザーのホームディレクトリを検索
   - `sudo find / -name "Caddyfile" 2>/dev/null`でシステム全体を検索

---

## プロジェクトを新規にセットアップする場合

プロジェクトディレクトリが見つからない場合、新規にセットアップする必要があります：

### ステップ1: プロジェクトディレクトリを作成

```bash
# appユーザーで実行する場合
sudo mkdir -p /home/app/toybox
sudo chown app:app /home/app/toybox
cd /home/app/toybox

# または、rootユーザーで実行する場合
mkdir -p /root/toybox
cd /root/toybox
```

### ステップ2: Gitリポジトリからクローン（推奨）

```bash
# Gitがインストールされているか確認
git --version

# リポジトリをクローン
git clone https://github.com/challenge-marlin/toybox.git .

# または、既存のリポジトリがある場合
git pull origin main
```

### ステップ3: WinSCPでファイルをアップロード

Gitリポジトリがない場合、WinSCPでファイルをアップロード：

1. WinSCPでサーバーに接続
2. ローカル側: `C:\github\toybox\`
3. サーバー側: `/home/app/toybox/` または `/root/toybox/`
4. すべてのファイルをアップロード

---

## よくある場所

プロジェクトディレクトリは以下の場所にある可能性があります：

```bash
# 1. appユーザーのホームディレクトリ
/home/app/toybox

# 2. rootユーザーのホームディレクトリ
/root/toybox

# 3. /optディレクトリ（アプリケーション用）
/opt/toybox

# 4. /var/wwwディレクトリ（Webアプリケーション用）
/var/www/toybox

# 5. /srvディレクトリ（サービス用）
/srv/toybox
```

---

## 次のステップ

プロジェクトディレクトリが見つかったら、以下の手順を実行してください：

1. プロジェクトディレクトリに移動
2. `CONNECTION_REFUSED_EMERGENCY_FIX.md`の手順を実行
3. Caddyコンテナを起動
