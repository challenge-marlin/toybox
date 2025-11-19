# クイックスタートガイド

Djangoサーバーを起動するための手順です。

## 前提条件

- Docker Desktopが起動していること
- 仮想環境が作成済みであること

## 起動手順

### 1. PostgreSQLとRedisをDockerで起動

```powershell
cd C:\github\toybox\backend
docker compose up -d db redis
```

これで、PostgreSQL（ポート5432）とRedis（ポート6379）が起動します。

### 2. Djangoサーバーを起動

新しいPowerShellウィンドウで：

```powershell
cd C:\github\toybox\backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### 3. アクセス

サーバーが起動したら、以下のURLにアクセス：

- **フロントエンド（マイページ）**: http://localhost:8000/me/
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **ヘルスチェック**: http://localhost:8000/api/health/

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
cd C:\github\toybox\backend
docker compose restart db redis
```

### マイグレーションが実行されていない場合

```powershell
cd C:\github\toybox\backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
```

### 全てのサービスを一度に起動する場合

```powershell
cd C:\github\toybox\backend
docker compose up -d
```

これで、PostgreSQL、Redis、Django（web）、Celery Worker、Celery Beatが全て起動します。

ただし、Djangoサーバーは通常、開発時はローカルで`python manage.py runserver`を実行する方が便利です。

