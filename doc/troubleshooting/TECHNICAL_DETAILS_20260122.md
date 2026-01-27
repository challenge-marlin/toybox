# 技術詳細：OGP設定作業からデータ損失までの技術的分析

**日付**: 2026年1月22日  
**対象**: 技術チーム、インフラチーム

---

## 1. 初期状態（17:00）

### システム構成
- **OS**: Ubuntu 24.04.3 LTS
- **サーバー**: ConoHa VPS（160.251.168.144）
- **Docker**: 複数バージョン（systemctl + Snap）← 後に判明
- **ディスク使用率**: 27.8% / 98.24GB

### Dockerコンテナ構成
```
- backend-web-1 (Django + Gunicorn)
- backend-db-1 (PostgreSQL 15)
- backend-redis-1 (Redis 7)
- backend-worker-1 (Celery worker)
- backend-beat-1 (Celery beat)
- toybox-caddy-1 (Caddy 2) - リバースプロキシ
```

---

## 2. OGP設定作業（17:00～17:30）

### 実施した変更

#### A. HTMLテンプレートの修正
**base.html**（全ページの基底テンプレート）:
```html
<!-- OGP Tags -->
<meta property="og:title" content="{% block og_title %}TOYBOX！{% endblock %}">
<meta property="og:description" content="{% block og_description %}TOYBOX！ - 創造の遊び場。ゲーム、画像、動画を作って共有しよう！{% endblock %}">
<meta property="og:image" content="{% block og_image %}https://toybox.ayatori-inc.co.jp/static/frontend/hero/toybox-ogp.png{% endblock %}">
<meta property="og:url" content="{% block og_url %}https://toybox.ayatori-inc.co.jp{{ request.path }}{% endblock %}">
```

#### B. 静的ファイルの配置
- **ファイル**: `toybox-ogp.png`（1200x630px、989KB）
- **配置先**: `backend/frontend/static/frontend/hero/`

#### C. collectstaticの実行
```bash
cd /var/www/toybox/backend
source venv/bin/activate
python manage.py collectstatic --noinput
```

**結果**: 
```
966 static files copied to '/var/www/toybox/backend/staticfiles'
```

#### D. Caddyfileの修正
```caddyfile
handle /static/* {
    root * /var/www/toybox/backend/staticfiles
    file_server
}
```

**この変更が、後の一連の問題の引き金となりました。**

---

## 3. 問題の発生と拡大（17:30～19:30）

### 3.1 最初の問題：docker-compose コマンドエラー

#### 実行したコマンド
```bash
docker-compose restart caddy
```

#### エラー
```
-bash: docker-compose: command not found
```

#### 原因
- Docker Composeのインストール方法が変わり、`docker compose`（スペース区切り）が正しい

---

### 3.2 ポート競合エラー

#### エラー内容
```
Error: failed to bind host port for 0.0.0.0:5432:172.20.0.2:5432/tcp: address already in use
Error: failed to bind host port for 0.0.0.0:6379:172.20.0.2:6379/tcp: address already in use
```

#### 原因分析
1. `docker-proxy` プロセスがポートを保持
2. 古いコンテナが停止していない
3. システムのRedisサービスが起動していた（PID 813）

#### 実施した対処（誤り）
```bash
docker rm -f $(docker ps -aq)
sudo pkill -9 docker-proxy
```

**問題点**: コンテナを強制削除したが、ポートは解放されず

---

### 3.3 iptablesの誤削除（重大インシデント）

#### 実行したコマンド
```bash
sudo iptables -t nat -F      # NATテーブルを全削除
sudo iptables -t filter -F   # FILTERテーブルを全削除
```

#### 意図
Dockerのネットワークルールをクリーンアップして、ポート競合を解決

#### 実際の影響
- ✅ Dockerのネットワークルール削除（意図通り）
- ❌ SSHポート（22番）の許可ルール削除（意図しない）
- ❌ HTTPSポート（443番）の許可ルール削除（意図しない）

#### 結果
```
ssh: connect to host 160.251.168.144 port 22: Connection timed out
```

**サーバーへのアクセスが完全に遮断**

---

### 3.4 iptablesエラーとシステム再起動

#### Dockerネットワークエラー
```
iptables failed: ... Chain 'DOCKER-ISOLATION-STAGE-2' does not exist
```

#### 原因
iptablesのチェーンが存在しないため、Dockerのネットワーク設定が失敗

#### 対処
```bash
sudo reboot
```

---

## 4. 読み取り専用ファイルシステム問題（18:00～20:30）

### 4.1 問題の詳細

#### エラー内容
```
error while creating mount source path '/var/www/toybox/backend': mkdir /var/www: read-only file system
```

#### 診断結果
```bash
mount | grep "/ "
# 出力: /dev/vda2 on / type ext4 (rw,relatime)
```

**矛盾**: `mount` コマンドでは `rw`（読み書き可能）と表示されるが、Dockerは読み取り専用エラーを報告

#### 試した対処法（すべて一時的な効果のみ）

1. **ファイルシステムの再マウント**（10回以上実施）
   ```bash
   mount -o remount,rw /
   ```
   - 効果: 一時的に動作するが、数分後に再び読み取り専用に戻る

2. **Dockerサービスの再起動**（7回実施）
   ```bash
   systemctl restart docker
   ```
   - 効果: 限定的

3. **システム再起動**（2回実施）
   ```bash
   sudo reboot
   ```
   - 効果: 一時的には改善するが、問題は再発

4. **Dockerストレージの再初期化**（2回実施）
   ```bash
   mv /var/lib/docker /var/lib/docker.backup.$(date +%Y%m%d_%H%M%S)
   mkdir /var/lib/docker
   systemctl restart docker
   ```
   - 効果: Dockerは起動するが、読み取り専用エラーは継続

---

### 4.2 コンテナ停止不能問題

#### 症状
```
Error response from daemon: cannot stop container: [container_id]: permission denied
Error response from daemon: cannot kill container: [container_id]: permission denied
```

#### 影響を受けたコンテナ
- `6419540e8ff1` (PostgreSQL)
- `d842e9b0f064` (Redis)
- `f8abeb80e221` (Worker)
- `4457a1dabbb7` (Beat)
- `a97eaed803e1` (Caddy)

#### 試した対処法（すべて失敗）
1. `docker stop` - permission denied
2. `docker kill` - permission denied
3. `docker rm -f` - permission denied
4. `--force-recreate` - 古いコンテナが停止できず失敗

#### 原因分析
- Dockerデーモン、カーネル、またはcgroupが不安定な状態
- ファイルシステムの問題が波及

---

## 5. 二重Dockerデーモン問題の発見（20:30）

### 発見した異常

#### プロセス確認結果
```bash
ps aux | grep dockerd

# 出力:
root   12388  /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root   18136  dockerd --group docker --exec-root=/run/snap.docker ...
```

**2つのDockerデーモンが同時に起動していた**

### 影響
- Dockerクライアントがどちらのデーモンに接続するか不安定
- コンテナ管理の競合
- `Cannot connect to the Docker daemon` エラー

### 解決
```bash
kill -9 18136
snap stop docker
snap disable docker
systemctl restart docker.socket
systemctl restart docker
```

---

## 6. 最終的な復旧作業（20:50～21:30）

### 6.1 docker-compose.yml の修正

#### 問題のあった設定
```yaml
volumes:
  - .:/app                                    # ← ホストマウント（read-only エラーの原因）
  - ./public/uploads:/app/public/uploads     # ← ホストマウント（read-only エラーの原因）
```

#### 修正後の設定
```yaml
volumes:
  - media_volume:/app/public/uploads         # ← Dockerボリュームに変更
# .:/app マウントを削除（本番環境では不要、コードはイメージにビルド済み）
```

---

### 6.2 docker-compose.prod.yml の修正

#### 修正前
```yaml
volumes:
  - ./Caddyfile:/etc/caddy/Caddyfile:ro                            # ← read-only エラー
  - ./backend/public/uploads:/app/public/uploads:ro                # ← read-only エラー
  - /var/www/toybox/backend/staticfiles:/var/www/.../staticfiles:ro # ← read-only エラー
```

#### 修正後
```yaml
build:
  context: .
  dockerfile: Dockerfile.caddy    # ← Caddyfileをイメージに埋め込み
volumes:
  - caddy-data:/data
  - caddy-config:/config
  - backend_static_volume:/app/staticfiles:ro  # ← Dockerボリュームに変更
```

---

### 6.3 Dockerfile.caddy の作成

```dockerfile
FROM caddy:2
COPY Caddyfile /etc/caddy/Caddyfile
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]
```

**目的**: ホストのファイルシステムマウントを避ける

---

### 6.4 Caddyfile の修正

#### 最終的な設定
```caddyfile
handle /static/* {
    root * /app/staticfiles
    uri strip_prefix /static
    file_server
}
```

**重要**: `uri strip_prefix /static` により、URLパスとファイルパスを正しくマッピング

---

### 6.5 最終的な復旧コマンド

```bash
# 1. Dockerサービスを停止
systemctl stop docker

# 2. すべてのコンテナを削除
rm -rf /var/lib/docker/containers/*    # ← ここでデータベースとの関連付けが失われた

# 3. Dockerサービスを起動
systemctl start docker

# 4. コンテナを再起動
cd /var/www/toybox/backend && docker compose up -d
cd /var/www/toybox && docker compose -f docker-compose.prod.yml up -d
```

**結果**: サイトは復旧したが、新しいPostgreSQLボリュームが作成され、データは空の状態

---

## 7. データ損失のメカニズム

### PostgreSQLボリュームの仕組み

#### 正常な状態
```
docker-compose.yml:
  volumes:
    - postgres_data:/var/lib/postgresql/data

Docker内部:
  コンテナID → ボリューム名 → 実際のデータパス
  6419540e8ff1 → postgres_data → /var/lib/docker/volumes/backend_postgres_data/_data
```

#### データ損失の流れ

1. **19:26頃**: `rm -rf /var/lib/docker/containers/*` 実行
   - コンテナのメタデータが削除される
   - **ボリュームとの関連付けが失われる**
   - しかし、ボリュームデータ自体は残っている

2. **20:57頃**: 新しいコンテナが起動
   - 同じ名前の `postgres_data` ボリュームを探す
   - 既存のボリュームが見つからない（関連付けが失われているため）
   - **新しい空のボリュームを作成**

3. **結果**:
   - 古いボリューム: `/var/lib/docker/volumes/backend_postgres_data/_data`（データあり、未使用）
   - 新しいボリューム: `/var/lib/docker/volumes/backend_postgres_data/_data`（データなし、使用中）

**実際には、同じパスが上書きされた可能性が高い**

---

## 8. バックアップの検証

### 作成されたバックアップ

#### 1. docker.backup.20260122_192134（19:21作成）
```bash
ls -la /var/lib/docker.backup.20260122_192134/volumes/
# 出力: metadata.db のみ（ボリュームデータなし）
```

#### 2. docker.backup.20260122_192555（19:25作成）
```bash
ls -la /var/lib/docker.backup.20260122_192555/volumes/
# 出力: metadata.db のみ（ボリュームデータなし）
```

#### 3. docker.backup.20260122_192834（19:28作成）
```bash
ls -la /var/lib/docker.backup.20260122_192834/volumes/
# 出力: metadata.db のみ（ボリュームデータなし）
```

### なぜボリュームデータがバックアップされなかったか

#### バックアップコマンド
```bash
mv /var/lib/docker /var/lib/docker.backup.20260122_192134
```

#### Dockerボリュームの実際の場所
Docker 20.10以降では、ボリュームデータは以下に保存される：
```
/var/lib/docker/volumes/[volume_name]/_data/
```

しかし、`mv` コマンド実行時に：
1. Dockerサービスが起動中だった可能性
2. ボリュームがマウント中だった
3. または、システムがメタデータのみコピーした

**結果**: `metadata.db` のみがコピーされ、実際のデータ（`_data/`ディレクトリ）はコピーされなかった

---

## 9. ファイルシステム読み取り専用問題の技術的分析

### 症状の詳細

#### 観察された動作
```bash
# コマンド1: システムレベルでの確認
mount | grep "/ "
# 出力: /dev/vda2 on / type ext4 (rw,relatime)  ← 読み書き可能

# コマンド2: 実際の書き込みテスト
echo "test" > /var/www/test-file && rm /var/www/test-file
# 出力: SUCCESS ← 書き込み可能

# コマンド3: Dockerのマウント操作
docker compose up -d
# 出力: error while creating mount source path: mkdir /var/www: read-only file system
```

**結論**: ファイルシステム自体は正常だが、Dockerのマウント処理で読み取り専用エラーが発生

### 考えられる原因

1. **Dockerストレージドライバーの状態不整合**
   - overlay2ストレージドライバーがファイルシステムの古い状態をキャッシュ
   - メタデータの破損

2. **カーネルレベルのマウント制限**
   - Dockerがマウント操作を行う際に、カーネルが拒否
   - SELinux、AppArmorなどのセキュリティモジュールの影響（可能性低）

3. **ディスクI/Oエラー**
   - dmesgでエラーは検出されなかったが、一時的なI/Oエラーの可能性

---

## 10. 復旧作業で実施した技術的対策

### 10.1 ホストマウントの排除

#### 理由
- read-only file systemエラーの回避
- 本番環境での安全性向上
- コンテナの移植性向上

#### 実装
すべてのホストマウントをDockerボリュームに変更：

**Before**:
```yaml
volumes:
  - .:/app                          # ← ホストの現在ディレクトリ
  - ./public/uploads:/app/uploads   # ← ホストのアップロードディレクトリ
  - ./Caddyfile:/etc/caddy/Caddyfile # ← ホストの設定ファイル
```

**After**:
```yaml
volumes:
  - media_volume:/app/uploads       # ← Dockerボリューム
# Caddyfileはイメージに埋め込み
# アプリケーションコードはビルド時にCOPY
```

---

### 10.2 Caddyfileのイメージ埋め込み

#### Dockerfile.caddy
```dockerfile
FROM caddy:2
COPY Caddyfile /etc/caddy/Caddyfile
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]
```

#### メリット
- ホストのファイルシステムマウント不要
- コンテナの自己完結性向上
- read-only file systemエラーの回避

---

### 10.3 静的ファイル配信の最適化

#### Dockerボリューム共有
```yaml
# backend/docker-compose.yml
web:
  volumes:
    - static_volume:/app/staticfiles

# docker-compose.prod.yml
caddy:
  volumes:
    - backend_static_volume:/app/staticfiles:ro  # ← backendのボリュームを参照

volumes:
  backend_static_volume:
    external: true
    name: backend_static_volume
```

#### Caddyfileの設定
```caddyfile
handle /static/* {
    root * /app/staticfiles
    uri strip_prefix /static
    file_server
}
```

**重要**: `uri strip_prefix` により、URL `/static/frontend/css/base.css` がファイル `/app/staticfiles/frontend/css/base.css` に正しくマッピング

---

## 11. データ損失の詳細

### 損失したデータ

#### ユーザーデータ
```sql
SELECT COUNT(*) FROM users;
-- 結果: 0（損失前: 推定100～1000件）
```

#### その他のデータ
- **投稿データ** (`submissions`): 0件
- **カード情報** (`cards`): 0件
- **ユーザーカード** (`user_cards`): 0件
- **リアクション** (`reactions`): 0件
- **セッション** (`django_session`): 0件

### データベース構造は保持

```sql
\dt
-- 24個のテーブルが存在（構造は正常）
```

**マイグレーションは正常に実行され、テーブル構造は復旧**

---

## 12. 最終的なシステム構成

### 復旧後のDocker構成

```yaml
# backend/docker-compose.yml
services:
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data  # ← 新しい空のボリューム

  redis:
    image: redis:7-alpine

  web:
    build: .
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/public/uploads       # ← ホストマウント排除

  worker:
    build: .
    volumes:
      - media_volume:/app/public/uploads

  beat:
    build: .
    # ボリュームなし（必要最小限）
```

```yaml
# docker-compose.prod.yml
services:
  caddy:
    build:
      dockerfile: Dockerfile.caddy
    volumes:
      - caddy-data:/data
      - caddy-config:/config
      - backend_static_volume:/app/staticfiles:ro
```

---

## 13. パフォーマンスと安定性

### 復旧後のパフォーマンス

#### 静的ファイル配信速度
```bash
curl -I https://toybox.ayatori-inc.co.jp/static/frontend/hero/toybox-ogp.png
# Content-Length: 989002 bytes
# 配信速度: 問題なし
```

#### Dockerボリュームのメリット
- ✅ ホストマウントより高速
- ✅ ファイルシステムの問題の影響を受けにくい
- ✅ コンテナ間での共有が容易

---

## 14. 今後の技術的推奨事項

### 14.1 バックアップ戦略

#### データベースバックアップスクリプト
```bash
#!/bin/bash
# /var/www/toybox/scripts/backup-database.sh

BACKUP_DIR="/var/www/toybox/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# データベースダンプ
docker exec backend-db-1 pg_dump -U postgres toybox > "$BACKUP_DIR/toybox_$DATE.sql"

# 圧縮
gzip "$BACKUP_DIR/toybox_$DATE.sql"

# 30日以上古いバックアップを削除
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: toybox_$DATE.sql.gz"
```

#### cron設定
```cron
# 毎日午前3時にバックアップ
0 3 * * * /var/www/toybox/scripts/backup-database.sh

# 毎週日曜日にボリュームバックアップ
0 2 * * 0 /var/www/toybox/scripts/backup-volumes.sh
```

---

### 14.2 Dockerボリュームバックアップスクリプト

```bash
#!/bin/bash
# /var/www/toybox/scripts/backup-volumes.sh

BACKUP_DIR="/var/www/toybox/backups/volumes"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQLボリュームをバックアップ
docker run --rm \
  -v backend_postgres_data:/data \
  -v "$BACKUP_DIR:/backup" \
  alpine tar czf "/backup/postgres_data_$DATE.tar.gz" /data

# メディアボリュームをバックアップ
docker run --rm \
  -v backend_media_volume:/data \
  -v "$BACKUP_DIR:/backup" \
  alpine tar czf "/backup/media_volume_$DATE.tar.gz" /data

echo "Volume backup completed: $DATE"
```

---

### 14.3 監視システムの導入

#### 監視項目
1. **ディスク使用率**: 80%で警告、90%でクリティカル
2. **ファイルシステムエラー**: dmesgを定期的にチェック
3. **Dockerコンテナの状態**: すべてのコンテナがHealthyか
4. **応答時間**: サイトの応答時間を監視
5. **エラーログ**: Djangoの500エラーを検知

#### 推奨ツール
- **Prometheus + Grafana**: メトリクス収集と可視化
- **Loki**: ログ集約
- **Alertmanager**: アラート通知（Slack、メール）

---

### 14.4 インフラの改善

#### ディスクの健全性チェック
```bash
# SMARTステータスの確認
sudo smartctl -a /dev/vda

# ファイルシステムチェック（再起動時）
# /etc/fstab に以下を追加
# /dev/vda2 / ext4 errors=remount-ro 0 1
```

#### Docker構成の改善
```yaml
# すべてのサービスにhealthcheckを追加
healthcheck:
  test: ["CMD-SHELL", "健全性チェックコマンド"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 40s
```

---

## 15. コマンド実行ログ（抜粋）

### 重要なコマンドの履歴

```
17:54 - python manage.py collectstatic --noinput
18:12 - docker rm -f $(docker ps -aq)
18:15 - sudo pkill -9 docker-proxy
18:20 - sudo iptables -t nat -F
18:20 - sudo iptables -t filter -F
18:30 - sudo reboot
18:49 - sudo reboot（2回目）
19:21 - mv /var/lib/docker /var/lib/docker.backup.20260122_192134
19:25 - mv /var/lib/docker /var/lib/docker.backup.20260122_192555
19:28 - mv /var/lib/docker /var/lib/docker.backup.20260122_192834
20:36 - systemctl stop docker
20:36 - rm -rf /var/lib/docker/containers/*  ← データ損失の直接的原因
20:37 - systemctl start docker
20:57 - docker compose up -d  ← 新しい空のボリュームが作成される
21:12 - python manage.py migrate  ← 新しいデータベースに構造を作成
21:15 - データ損失を確認（ユーザー数: 0）
```

---

## 16. システムリソース状態

### ディスク使用状況
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda2        99G   28G   67G  30% /
```

### メモリ使用状況
```
Memory usage: 25%
Swap usage: 0%
```

### Dockerプロセス
```
dockerd (PID: 12388) - 正常稼働中
containerd (PID: xxxx) - 正常稼働中
```

---

## 17. セキュリティ影響

### 漏洩の可能性
- ❌ **外部への情報漏洩なし**
- ❌ **不正アクセスなし**
- ✅ データは削除されたが、外部に流出していない

### iptablesルールの復元
```bash
# 現在のiptablesルール（復元済み）
iptables -A INPUT -p tcp --dport 22 -j ACCEPT   # SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT   # HTTP
iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

---

## 付録A：エラーメッセージ一覧

### read-only file system エラー
```
Error response from daemon: error while creating mount source path '/var/www/toybox/backend': mkdir /var/www: read-only file system
Error response from daemon: error while creating mount source path '/var/www/toybox/Caddyfile': mkdir /var/www: read-only file system
```

### permission denied エラー
```
Error response from daemon: cannot stop container: [id]: permission denied
Error response from daemon: cannot kill container: [id]: permission denied
```

### iptables エラー
```
iptables failed: ... Chain 'DOCKER-ISOLATION-STAGE-2' does not exist
```

### データベースエラー
```
django.db.utils.ProgrammingError: relation "django_session" does not exist
```

---

## 付録B：変更されたファイルの完全な差分

### 1. backend/docker-compose.yml

**削除された設定**:
```yaml
- .:/app                                    # 行34, 56, 75
- ./public/uploads:/app/public/uploads     # 行37, 58
```

**追加された設定**:
```yaml
- media_volume:/app/public/uploads         # 行34（webサービス）
```

**コメントアウトされた設定**:
```yaml
# nginx:  # 行86～96（本番環境では使用しないため）
```

### 2. docker-compose.prod.yml

**変更前**:
```yaml
caddy:
  image: caddy:2
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile:ro
```

**変更後**:
```yaml
caddy:
  build:
    context: .
    dockerfile: Dockerfile.caddy
  volumes:
    - caddy-data:/data
    - caddy-config:/config
    - backend_static_volume:/app/staticfiles:ro
```

### 3. Caddyfile

**変更前**:
```caddyfile
handle /static/* {
    root * /var/www/toybox/backend/staticfiles
    file_server
}
```

**変更後**:
```caddyfile
handle /static/* {
    root * /app/staticfiles
    uri strip_prefix /static
    file_server
}
```

### 4. 新規作成ファイル

#### Dockerfile.caddy
```dockerfile
FROM caddy:2
COPY Caddyfile /etc/caddy/Caddyfile
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile"]
```

---

## 付録C：復旧後のヘルスチェック

### すべてのコンテナが正常稼働
```bash
docker ps
# 出力:
# toybox-caddy-1    Up
# backend-web-1     Up
# backend-db-1      Up (healthy)
# backend-redis-1   Up (healthy)
# backend-worker-1  Up
# backend-beat-1    Up
```

### サイトが正常にアクセス可能
```bash
curl -I https://toybox.ayatori-inc.co.jp
# HTTP/2 200
```

### 静的ファイルが正常に配信
```bash
curl -I https://toybox.ayatori-inc.co.jp/static/frontend/css/base.css
# HTTP/2 200

curl -I https://toybox.ayatori-inc.co.jp/static/frontend/hero/toybox-ogp.png
# HTTP/2 200 (989KB)
```

### OGPが正常に動作
- ✅ メタタグが正しく出力
- ✅ OGP画像が配信
- ✅ Twitter Card対応

---

## 結論

今回のインシデントは、以下の複合的な要因により発生しました：

1. **サーバーインフラの潜在的な問題**（ファイルシステムの不安定性）
2. **運用体制の不備**（バックアップシステムの欠如）
3. **緊急時の判断ミス**（iptables削除、コンテナディレクトリ削除）

**教訓**: 
- 本番環境での作業は、必ずバックアップを取ってから実施
- トラブル時は、段階的に対処し、強制的な削除は最終手段とする
- 定期的なバックアップとテストが不可欠

**次のステップ**: 
- バックアップシステムの即時構築
- 監視システムの導入
- ディスクの健全性チェック

---

**レポート作成日**: 2026年1月22日 21:30  
**ステータス**: サイト復旧済み、データ損失確認済み
