# ポート確認とCaddy起動手順

## nginxサービスが存在しない場合の手順

### ステップ1: ポート80/443を確認

VNCコンソールで以下を実行：

```bash
# ポート80/443を使用しているプロセスを確認
netstat -tlnp | grep -E ':80|:443'
# または
ss -tlnp | grep -E ':80|:443'

# Dockerコンテナがポートを使用しているか確認
docker ps | grep -E '80|443'
```

### ステップ2: Dockerコンテナのnginxを確認

```bash
# 実行中の全てのコンテナを確認
docker ps -a

# nginxコンテナがあるか確認
docker ps -a | grep nginx

# nginxコンテナがある場合は停止
docker stop $(docker ps -q --filter "ancestor=nginx") 2>/dev/null
docker rm $(docker ps -aq --filter "ancestor=nginx") 2>/dev/null
```

### ステップ3: プロジェクトディレクトリを確認

```bash
# プロジェクトディレクトリを探す
ls -la /home/app/
ls -la /root/

# または、Caddyfileを探す
find / -name "Caddyfile" -type f 2>/dev/null

# 見つかったディレクトリに移動
# 例: cd /home/app/toybox
```

### ステップ4: Caddyを起動

```bash
# プロジェクトディレクトリに移動（上で見つけたパス）
cd /home/app/toybox  # または適切なパス

# 現在のディレクトリとファイルを確認
pwd
ls -la

# Caddyfileが存在するか確認
cat Caddyfile

# Docker Composeを起動
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy
```

### ステップ5: アクセステスト

```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp
```

## まとめ

1. ✅ nginxサービスは存在しない（問題なし）
2. ⏭️ ポート80/443を確認
3. ⏭️ Dockerコンテナのnginxを確認
4. ⏭️ プロジェクトディレクトリを確認
5. ⏭️ Caddyを起動

