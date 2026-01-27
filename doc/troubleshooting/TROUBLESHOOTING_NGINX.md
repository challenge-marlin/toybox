# nginx競合問題の解決手順

## 問題
ToyBoxにアクセスすると、nginxのエラーメッセージが表示される：
```
An error occurred.
Sorry, the page you are looking for is currently unavailable.
Please try again later.
If you are the system administrator of this resource then you should check the error log for details.
Faithfully yours, nginx.
```

## 原因
本番サーバーでnginxがポート80/443を占有しており、Caddyが正しく起動できていません。

## 解決手順

### 1. サーバーにSSHで接続
```bash
ssh app@<サーバーIP>
```

### 2. nginxの状態を確認
```bash
# nginxが動いているか確認
sudo systemctl status nginx

# または、dockerコンテナでnginxが動いているか確認
docker ps | grep nginx
```

### 3. nginxを停止

#### 方法A: システムレベルのnginxを停止（推奨）
```bash
# nginxを停止
sudo systemctl stop nginx

# nginxを無効化（再起動時に自動起動しないようにする）
sudo systemctl disable nginx

# 確認
sudo systemctl status nginx
```

#### 方法B: Dockerコンテナのnginxを停止
```bash
# nginxコンテナを停止・削除
docker stop $(docker ps -q --filter "ancestor=nginx")
docker rm $(docker ps -aq --filter "ancestor=nginx")

# または、docker-composeでnginxが動いている場合
docker compose down
```

### 4. ポート80/443が解放されているか確認
```bash
# ポート80を確認
sudo lsof -i :80
sudo netstat -tlnp | grep :80

# ポート443を確認
sudo lsof -i :443
sudo netstat -tlnp | grep :443
```

### 5. Caddyコンテナを再起動
```bash
cd ~/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 6. Caddyが正しく起動しているか確認
```bash
# Caddyコンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps caddy

# Caddyのログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f caddy

# Caddyfileの構文を確認（Caddyコンテナ内で）
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
```

### 7. アクセステスト
```bash
# ローカルからテスト
curl -I http://toybox.ayatori-inc.co.jp
curl -I https://toybox.ayatori-inc.co.jp

# ヘルスチェック
curl http://toybox.ayatori-inc.co.jp/health
```

## nginxを完全に削除する場合（オプション）

もしnginxが不要であれば、以下のコマンドで削除できます：

```bash
# Ubuntu/Debianの場合
sudo apt remove --purge nginx nginx-common
sudo apt autoremove

# 設定ファイルも削除
sudo rm -rf /etc/nginx
sudo rm -rf /var/log/nginx
```

## 確認事項

- [ ] nginxが停止している
- [ ] ポート80/443が解放されている
- [ ] Caddyコンテナが起動している
- [ ] Caddyfileの構文が正しい
- [ ] ブラウザで `https://toybox.ayatori-inc.co.jp` にアクセスできる

## トラブルシューティング

### Caddyが起動しない場合
1. Caddyfileの構文を確認：
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
   ```

2. ポートの競合を確認：
   ```bash
   sudo lsof -i :80
   sudo lsof -i :443
   ```

3. Caddyのログを確認：
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml logs caddy
   ```

### HTTPS証明書が発行されない場合
1. DNSのAレコードが正しく設定されているか確認
2. ポート80/443が外部からアクセス可能か確認（ファイアウォール設定）
3. Let's Encryptのレート制限に掛かっていないか確認（時間を置いて再試行）

