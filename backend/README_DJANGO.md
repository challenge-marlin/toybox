# ToyBox Django Backend

[![Tests](https://github.com/YOUR_USERNAME/toybox/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/toybox/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/YOUR_USERNAME/toybox/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/toybox)

Django 5 + DRF + PostgreSQL + Celery + Redis 構成のバックエンドAPI

## プロジェクト構成

- **プロジェクト名**: toybox
- **アプリ**:
  - `users`: ユーザー認証・プロフィール管理
  - `submissions`: 投稿機能
  - `lottery`: 抽選・報酬処理
  - `gamification`: 称号・カード収集
  - `sharing`: Discordシェア
  - `adminpanel`: 管理画面UI
  - `frontend`: 一般UI（Djangoテンプレート）

## セットアップ

### Dockerでの起動（推奨）

#### 初回セットアップ

1. **環境変数の設定**

```bash
cd backend
cp env.sample .env
# .envファイルを編集して必要な値を設定
```

2. **Docker Composeで起動**

```bash
cd backend
make up
# または
docker compose up -d
```

**注意**: `backend/`ディレクトリから実行してください。ルートディレクトリの`docker-compose.yml`は既存のNext.js/Expressプロジェクト用です。

#### 次回から起動する場合

PCを再起動した後や、Dockerコンテナを停止した後に再度起動する場合：

**Windows PowerShell:**
```powershell
cd C:\github\toybox\backend
.\make.ps1 up
# または
docker compose up -d

再起動
# backendディレクトリで実行
docker compose restart
```

**Linux/macOS:**
```bash
cd backend
make up
# または
docker compose up -d
```

これだけで、PostgreSQL、Redis、Django Webサーバー、Celery Worker/Beatがすべて起動します。

3. **マイグレーション実行**

```bash
cd backend
make migrate
# または
docker compose exec web python manage.py migrate
```

4. **スーパーユーザー作成**

```bash
make superuser
# または
docker compose -f docker-compose.yml exec web python manage.py createsuperuser
```

5. **アクセス**

- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- API Schema: http://localhost:8000/api/schema/swagger-ui/
- Health Check: http://localhost:8000/api/health/

### 非Dockerでのローカル起動

1. **必要な環境**

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

2. **仮想環境の作成と有効化**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **依存関係のインストール**

```bash
pip install -r requirements.txt
```

4. **環境変数の設定**

```bash
cd backend
cp env.sample .env
# .envファイルを編集
```

5. **データベースのセットアップ**

```bash
# PostgreSQLにデータベースを作成
createdb toybox

# マイグレーション実行
python manage.py migrate
```

6. **Redisの起動**

```bash
redis-server
```

7. **開発サーバーの起動**

```bash
# Django開発サーバー
python manage.py runserver

# 別ターミナルでCelery Worker
celery -A toybox worker --loglevel=info

# 別ターミナルでCelery Beat（定期タスク用）
celery -A toybox beat --loglevel=info
```

## サーバーの再起動方法

### ローカルで起動している場合（推奨・開発時）

1. **サーバーを停止**
   - サーバーが起動しているターミナルで `Ctrl + C` を押す
   - Windowsの場合は `Ctrl + Break` も可

2. **サーバーを再起動**
   ```bash
   # 仮想環境を有効化（必要に応じて）
   source venv/bin/activate  # Windows: venv\Scripts\Activate.ps1
   
   # サーバーを起動
   python manage.py runserver
   ```

### Dockerで起動している場合

```bash
# Djangoコンテナのみ再起動
docker compose restart web

# または、すべてのサービスを再起動
docker compose restart
```

### コード変更後の再起動が必要な場合

Djangoの開発サーバー（`runserver`）は通常、コード変更を自動検知して再読み込みしますが、以下の場合は手動で再起動が必要です：

- 新しいモデルフィールドを追加した場合
- 設定ファイル（`settings.py`など）を変更した場合
- URLルーティングを変更した場合
- 依存関係を追加・更新した場合
- コードの変更が反映されない場合

**再起動手順**:
1. `Ctrl + C` でサーバーを停止
2. `python manage.py runserver` で再起動

## 主要コマンド

### Linux/macOS (makeコマンド使用)

```bash
make up              # 全サービス起動
make down            # 全サービス停止
make restart         # 全サービス再起動
make logs            # ログ表示
make shell           # Django shell起動
make migrate         # マイグレーション実行
make makemigrations  # マイグレーションファイル作成
make superuser       # スーパーユーザー作成
make test            # テスト実行
make fmt             # コードフォーマット
make clean           # キャッシュファイル削除
```

### Windows PowerShell

```powershell
.\make.ps1 up              # 全サービス起動
.\make.ps1 down            # 全サービス停止
.\make.ps1 restart         # 全サービス再起動
.\make.ps1 logs            # ログ表示
.\make.ps1 shell           # Django shell起動
.\make.ps1 migrate         # マイグレーション実行
.\make.ps1 makemigrations  # マイグレーションファイル作成
.\make.ps1 superuser       # スーパーユーザー作成
.\make.ps1 test            # テスト実行
.\make.ps1 fmt             # コードフォーマット
.\make.ps1 clean           # キャッシュファイル削除
```

### 直接docker composeコマンドを使用する場合

```bash
# 全サービス起動
docker compose -f docker-compose.yml up -d

# マイグレーション実行
docker compose -f docker-compose.yml exec web python manage.py migrate

# スーパーユーザー作成
docker compose -f docker-compose.yml exec web python manage.py createsuperuser
```

## APIエンドポイント

### 認証
- `POST /api/auth/login/` - ログイン（JWT取得）
- `POST /api/auth/refresh/` - トークンリフレッシュ
- `POST /api/auth/register/` - ユーザー登録
- `POST /api/auth/logout/` - ログアウト
- `GET /api/auth/me/` - 現在のユーザー情報

### ユーザー
- `GET /api/user/me/` - 自分のメタデータ
- `GET /api/user/profile/<anon_id>/` - 公開プロフィール
- `PATCH /api/user/profile/` - プロフィール更新

### 投稿
- `POST /api/submit/` - 投稿作成
- `GET /api/submissions/me/` - 自分の投稿一覧
- `GET /api/submissions/user/<anon_id>/` - ユーザー別投稿一覧
- `GET /api/submissions/<id>/` - 投稿詳細
- `POST /api/submissions/<id>/like/` - いいね
- `DELETE /api/submissions/<id>/like/` - いいね解除
- `DELETE /api/submissions/<id>/delete/` - 投稿削除

### フィード
- `GET /api/feed/` - 全体フィード

### お題
- `GET /api/topic/work/` - 業務系お題
- `GET /api/topic/play/` - お遊び系お題

### カード
- `POST /api/cards/generate/` - カード生成
- `GET /api/cards/me/` - 自分のカード一覧
- `GET /api/cards/summary/` - カードサマリー

### 通知
- `GET /api/notifications/` - 通知一覧
- `POST /api/notifications/read/` - 通知既読化

### ランキング
- `GET /api/ranking/daily/` - デイリーランキング
- `GET /api/submitters/today/` - 当日の提出者一覧

### シェア
- `POST /api/share/discord/` - Discordシェア

### ヘルスチェック
- `GET /api/health/` - ヘルスチェック
- `GET /api/health/ready/` - レディネスチェック

## 開発

### テスト実行

```bash
make test
# または
python manage.py test
```

### コードフォーマット

```bash
make fmt
```

### Django Admin

1. スーパーユーザーを作成
2. http://localhost:8000/admin/ にアクセス

## 本番環境セットアップ

### 前提条件

- Docker と Docker Compose がインストール済み
- ドメイン名が設定済み（HTTPS用）
- AWS S3 を使用する場合は認証情報を準備

### 1. 環境変数の設定

`backend/env.prod.sample`をコピーして`.env`ファイルを作成し、本番環境用の値を設定：

```bash
cd backend
cp env.prod.sample .env
# .envファイルを編集して必要な値を設定
```

### 2. 本番用Dockerイメージのビルド

```bash
make build
# または
docker build -f Dockerfile.prod -t toybox:latest .
```

### 3. データベースのマイグレーション

```bash
make migrate
# または
docker compose exec web python manage.py migrate
```

### 4. 静的ファイルの収集

```bash
make collectstatic
# または
docker compose exec web python manage.py collectstatic --noinput
```

### 5. スーパーユーザーの作成

```bash
make createadmin
# または
docker compose exec web python manage.py createsuperuser
```

### 6. サービスの起動

```bash
docker compose up -d
```

### 7. ヘルスチェック確認

```bash
curl http://localhost/api/health/
# または
docker compose exec web python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health/').read())"
```

### 8. Nginx設定のカスタマイズ

`nginx/conf/default.conf`を編集して、ドメイン名やSSL証明書の設定を追加：

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... 既存の設定 ...
}
```

### 9. SSL証明書の設定（Let's Encrypt）

```bash
# Certbotを使用してSSL証明書を取得
docker run -it --rm \
  -v certbot-certs:/etc/letsencrypt \
  -v certbot-www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d yourdomain.com -d www.yourdomain.com
```

### 10. ログの確認

```bash
# すべてのサービスのログ
docker compose logs -f

# 特定のサービスのログ
docker compose logs -f web
docker compose logs -f worker
```

### 11. バックアップ

```bash
# データベースのバックアップ
docker compose exec db pg_dump -U postgres toybox > backup_$(date +%Y%m%d_%H%M%S).sql

# メディアファイルのバックアップ（S3未使用の場合）
docker compose exec web tar -czf /tmp/media_backup.tar.gz /app/public/uploads
```

### トラブルシューティング

#### ヘルスチェックが失敗する場合

```bash
# コンテナの状態を確認
docker compose ps

# ログを確認
docker compose logs web

# 手動でヘルスチェック
docker compose exec web curl http://localhost:8000/api/health/
```

#### 静的ファイルが表示されない場合

```bash
# 静的ファイルを再収集
make collectstatic
```

#### データベース接続エラー

```bash
# データベースの状態を確認
docker compose exec db pg_isready -U postgres

# 接続テスト
docker compose exec web python manage.py dbshell
```

## ライセンス

（ライセンス情報を記載）

