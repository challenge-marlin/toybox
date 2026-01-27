# VNCコンソールから直接nginx問題を解決する手順

## 方針変更
SSH接続の問題は後回しにして、**VNCコンソールから直接nginxを停止し、Caddyを起動する**

## 手順

### ステップ1: VNCコンソールでnginxを確認・停止

ConoHa管理画面 → VNCコンソール → rootユーザーでログイン

以下のコマンドを実行：

```bash
# 1. nginxの状態を確認
systemctl status nginx

# 2. nginxが動いている場合は停止
systemctl stop nginx
systemctl disable nginx

# 3. ポート80/443が使用されているか確認
netstat -tlnp | grep -E ':80|:443'
# または
ss -tlnp | grep -E ':80|:443'

# 4. nginxプロセスが残っていないか確認
ps aux | grep nginx

# 5. nginxプロセスが残っている場合は強制終了
pkill -9 nginx
```

### ステップ2: Dockerとコンテナの状態を確認

```bash
# Dockerがインストールされているか確認
docker --version

# 実行中のコンテナを確認
docker ps -a

# toyboxプロジェクトがあるか確認
ls -la /home/app/toybox
# または
ls -la /root/toybox
```

### ステップ3: プロジェクトディレクトリに移動してCaddyを起動

```bash
# プロジェクトディレクトリに移動（存在する場所を確認して移動）
cd /home/app/toybox
# または
cd /root/toybox

# 現在のディレクトリを確認
pwd

# docker-composeファイルが存在するか確認
ls -la docker-compose*.yml

# Caddyfileが存在するか確認
ls -la Caddyfile

# コンテナを停止（既存のコンテナがある場合）
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Caddyを起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy
```

### ステップ4: アクセステスト

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# ヘルスチェック
curl http://toybox.ayatori-inc.co.jp/health
```

## プロジェクトディレクトリが見つからない場合

```bash
# プロジェクトを探す
find / -name "docker-compose.yml" -type f 2>/dev/null | grep toybox

# または、GitHubからクローン
cd /home/app
git clone https://github.com/challenge-marlin/toybox.git
cd toybox
```

## まとめ

1. VNCコンソールでnginxを停止
2. ポート80/443が解放されているか確認
3. Dockerコンテナを起動
4. Caddyが正しく起動しているか確認
5. ブラウザでアクセステスト

SSH接続の問題は後で解決できます。まずはnginxの問題を解決しましょう！

