# ToyBox

Django 5 + DRF + PostgreSQL + Celery + Redis 構成のWebアプリケーション

## 📋 目次

- [プロジェクト構成](#プロジェクト構成)
- [クイックスタート](#クイックスタート)
- [開発環境のセットアップ](#開発環境のセットアップ)
- [デプロイメント](#デプロイメント)
- [トラブルシューティング](#トラブルシューティング)
- [ドキュメント](#ドキュメント)

## プロジェクト構成

- **Backend**: Django 5 + DRF + PostgreSQL + Celery + Redis
- **Frontend**: Django Templates（HTMX対応）

### ディレクトリ構成

```
toybox/
├── backend/              # Django バックエンド
│   ├── users/           # ユーザー認証・プロフィール
│   ├── submissions/     # 投稿機能
│   ├── lottery/         # 抽選・報酬処理
│   ├── gamification/    # 称号・カード収集
│   ├── sharing/         # Discordシェア
│   ├── adminpanel/      # 管理画面UI
│   └── frontend/         # 一般UI（Djangoテンプレート）
├── docs/                 # 移行ドキュメント
├── doc/                  # その他のドキュメント
│   ├── legacy/          # Django移行前のコード
│   ├── deployment/      # デプロイメント関連
│   ├── setup/           # セットアップ関連
│   └── troubleshooting/ # トラブルシューティング
└── scripts/              # ユーティリティスクリプト
```

## クイックスタート

### Dockerでの起動（推奨）

```bash
cd backend
docker compose up -d
```

サーバーが起動したら、以下のURLにアクセス：

- **フロントエンド（マイページ）**: http://localhost:8000/me/
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **ヘルスチェック**: http://localhost:8000/api/health/

### ローカル開発環境での起動

#### 1. PostgreSQLとRedisをDockerで起動

```powershell
cd backend
docker compose up -d db redis
```

#### 2. Djangoサーバーを起動

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### サーバーの再起動方法

#### ローカルで起動している場合

1. サーバーを停止: `Ctrl + C`（Windowsの場合は `Ctrl + Break` も可）
2. サーバーを再起動:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

#### Dockerで起動している場合

```powershell
cd backend
docker compose restart web
```

すべてのサービスを再起動する場合：

```powershell
cd backend
docker compose restart
```

## 開発環境のセットアップ

### 前提条件

- Python 3.11以上
- Docker Desktop
- PostgreSQL 15
- Redis 7

### セットアップ手順

1. **仮想環境の作成と有効化**

   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **依存関係のインストール**

   ```powershell
   pip install -r requirements.txt
   ```

3. **環境変数の設定**

   ```powershell
   cp env.sample .env
   # .envファイルを編集して必要な設定を追加
   ```

4. **データベースのマイグレーション**

   ```powershell
   python manage.py migrate
   ```

5. **スーパーユーザーの作成（オプション）**

   ```powershell
   python manage.py createsuperuser
   ```

### 環境変数の設定

`.env`ファイルに以下の設定が必要です：

```env
# Database
DB_NAME=toybox
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Email (SMTP)
EMAIL_HOST=CONOHAのSMTP
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@ayatori-inc.co.jp
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@ayatori-inc.co.jp
CONTACT_EMAIL=maki@ayatori-inc.co.jp

# Discord
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_BOT_TOKEN=your-bot-token
```

**重要**: Docker Composeは`backend/.env`ファイルを読み込みます。ルートディレクトリの`.env`は使用されません。

## デプロイメント

### 自動デプロイ（推奨）

GitHubにプッシュするだけで自動的に本番環境にデプロイされます。

詳細は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) を参照してください。

### 手動デプロイ

#### 本番環境（手動）

```bash
# サーバー側で実行
cd ~/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

または、ローカルからデプロイスクリプトを実行：

```bash
./scripts/deploy.sh
```

### サーバーへの接続

#### SSH接続

```bash
ssh app@160.251.168.144
```

初回接続時は`root`ユーザーで接続：

```bash
ssh root@160.251.168.144
```

接続できない場合は、VNCコンソール経由でSSH設定を確認してください。

詳細は [SSH_CONNECTION_GUIDE.md](./SSH_CONNECTION_GUIDE.md) を参照してください。

### ConoHaでのホスティング

ConoHa VPSでのデプロイ手順は [ホスティング.md](./ホスティング.md) を参照してください。

## トラブルシューティング

### PostgreSQL接続エラーが発生する場合

1. Docker Desktopが起動しているか確認
2. PostgreSQLコンテナが起動しているか確認：

   ```powershell
   docker ps
   ```

   `backend-db-1`が表示されていればOKです。

3. コンテナを再起動：

   ```powershell
   cd backend
   docker compose restart db redis
   ```

### マイグレーションが実行されていない場合

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
```

### メール送信が失敗する場合

1. `.env`ファイルの`EMAIL_HOST_USER`と`EMAIL_HOST_PASSWORD`が設定されているか確認
2. `backend/.env`ファイルを確認（Docker Composeはこのファイルを読み込みます）
3. コンテナを再起動：

   ```powershell
   docker compose restart web
   ```

詳細は [backend/EMAIL_DIAGNOSIS.md](./backend/EMAIL_DIAGNOSIS.md) を参照してください。

### nginxとCaddyの競合

本番環境でnginxがポート80/443を占有している場合、Caddyが起動できません。

1. nginxを停止：

   ```bash
   sudo systemctl stop nginx
   sudo systemctl disable nginx
   ```

2. Caddyを起動：

   ```bash
   cd ~/toybox
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

## ドキュメント

### 主要ドキュメント

- **開発ガイド**: [backend/README_DJANGO.md](./backend/README_DJANGO.md)
- **移行ドキュメント**: [docs/migration/](./docs/migration/)
- **レガシーコード**: [doc/legacy/](./doc/legacy/)（Django移行前のコード）
- **デプロイメント**: [doc/deployment/](./doc/deployment/)
- **セットアップ**: [doc/setup/](./doc/setup/)
- **トラブルシューティング**: [doc/troubleshooting/](./doc/troubleshooting/)

### その他のドキュメント

- **SSH接続ガイド**: [SSH_CONNECTION_GUIDE.md](./SSH_CONNECTION_GUIDE.md)
- **ホスティング手順**: [ホスティング.md](./ホスティング.md)
- **リファクタリング完了報告**: [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)
- **現在の状態**: [CURRENT_STATUS.md](./CURRENT_STATUS.md)

## 機能一覧

- ✅ ユーザー認証・プロフィール管理
- ✅ 投稿機能（画像アップロード対応）
- ✅ いいね機能・通知
- ✅ みんなの投稿フィード
- ✅ 抽選・報酬処理
- ✅ 称号・カード収集（ゲーミフィケーション）
- ✅ Discordシェア機能
- ✅ 管理画面

## 技術スタック

- **Backend**: Django 5, Django REST Framework
- **Database**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery
- **Web Server**: Gunicorn
- **Reverse Proxy**: Caddy（本番環境）
- **Container**: Docker, Docker Compose

## ライセンス

（ライセンス情報を追加）
