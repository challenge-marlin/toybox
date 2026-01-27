# Djangoサーバーの起動方法

`ERR_CONNECTION_REFUSED`エラーは、Djangoサーバーが起動していないことを示しています。

## 起動手順

### PowerShellで実行

**1. 仮想環境を有効化してDjangoサーバーを起動**

```powershell
cd C:\github\toybox\backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### 起動確認

サーバーが起動すると、以下のようなメッセージが表示されます：

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
January 01, 2025 - 12:00:00
Django version 5.2.8, using settings 'toybox.settings.dev'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### アクセス

サーバーが起動したら、以下のURLにアクセスできます：

- **フロントエンド（マイページ）**: http://localhost:8000/me/
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **ヘルスチェック**: http://localhost:8000/api/health/

## トラブルシューティング

### 1. データベース接続エラーが発生する場合

PostgreSQLが起動していない可能性があります。以下のいずれかを実行：

**オプションA: DockerでPostgreSQLを起動**

```powershell
cd C:\github\toybox\backend
docker compose up -d db redis
```

**オプションB: ローカルにPostgreSQLをインストールして起動**

PostgreSQLをインストールし、サービスとして起動してください。

### 2. 環境変数が設定されていない場合

`.env`ファイルを作成：

```powershell
cd C:\github\toybox\backend
copy env.sample .env
# .envファイルを編集して必要な値を設定
```

最低限必要な設定：

```env
DB_NAME=toybox
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key-here
```

### 3. マイグレーションが実行されていない場合

```powershell
cd C:\github\toybox\backend
.\venv\Scripts\Activate.ps1
python manage.py migrate
```

### 4. 静的ファイルのエラーが発生する場合

```powershell
cd C:\github\toybox\backend
.\venv\Scripts\Activate.ps1
python manage.py collectstatic --noinput
```

## サーバーの停止

サーバーを停止するには、サーバーが起動しているターミナルで：

- `Ctrl + C` を押す
- または `Ctrl + Break` を押す

## バックグラウンドで起動する場合

PowerShellでバックグラウンド起動：

```powershell
cd C:\github\toybox\backend
.\venv\Scripts\Activate.ps1
Start-Process python -ArgumentList "manage.py", "runserver" -NoNewWindow
```

停止する場合は、プロセスを確認して停止：

```powershell
Get-Process python | Where-Object {$_.Path -like "*toybox*"} | Stop-Process
```

