# Django バックエンド起動ガイド

## 方法1: Dockerを使った起動（推奨）

### 前提条件
- Docker Desktop がインストール済みで起動していること

### 起動手順

1. **環境変数ファイルの確認**
   ```powershell
   cd C:\github\toybox\backend
   # .envファイルが存在することを確認（存在しない場合は下記を実行）
   Copy-Item env.sample .env
   ```

2. **Docker Composeで起動**
   ```powershell
   cd C:\github\toybox\backend
   .\make.ps1 up
   # または
   docker compose up -d
   ```

3. **マイグレーション実行**
   ```powershell
   .\make.ps1 migrate
   # または
   docker compose exec web python manage.py migrate
   ```

4. **スーパーユーザー作成（初回のみ）**
   ```powershell
   .\make.ps1 superuser
   # または
   docker compose exec web python manage.py createsuperuser
   ```

5. **アクセス**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Health Check: http://localhost:8000/api/health/

### 便利なコマンド

```powershell
.\make.ps1 logs          # ログを表示
.\make.ps1 down          # 全サービスを停止
.\make.ps1 restart       # 全サービスを再起動
.\make.ps1 shell         # Django shellを起動
```

---

## 方法2: ローカルで起動（Dockerなし）

### 前提条件
- Python 3.11+
- PostgreSQL 15+ がインストール済みで起動していること
- Redis 7+ がインストール済みで起動していること

### 起動手順

1. **仮想環境の有効化**
   ```powershell
   cd C:\github\toybox\backend
   .\venv\Scripts\Activate.ps1
   ```

2. **依存関係のインストール（初回のみ）**
   ```powershell
   pip install -r requirements.txt
   ```

3. **環境変数の設定**
   ```powershell
   # .envファイルが存在することを確認（存在しない場合は下記を実行）
   Copy-Item env.sample .env
   # .envファイルを編集してDB_HOSTをlocalhostに変更
   ```

   `.env`ファイルの`DB_HOST`を`localhost`に変更：
   ```
   DB_HOST=localhost
   ```

4. **PostgreSQLデータベースの作成**
   ```powershell
   # PostgreSQLが起動していることを確認
   createdb toybox
   # または、PostgreSQLに接続して作成
   ```

5. **マイグレーション実行**
   ```powershell
   python manage.py migrate
   ```

6. **スーパーユーザー作成（初回のみ）**
   ```powershell
   python manage.py createsuperuser
   ```

7. **Redisの起動**
   ```powershell
   # 別のターミナルでRedisを起動
   redis-server
   ```

8. **開発サーバーの起動**
   ```powershell
   python manage.py runserver
   ```

9. **Celery Workerの起動（別ターミナル）**
   ```powershell
   .\venv\Scripts\Activate.ps1
   celery -A toybox worker --loglevel=info
   ```

10. **Celery Beatの起動（別ターミナル、定期タスク用）**
    ```powershell
    .\venv\Scripts\Activate.ps1
    celery -A toybox beat --loglevel=info
    ```

---

## トラブルシューティング

### Docker Desktopが起動しない場合
1. Docker Desktopをスタートメニューから起動
2. タスクトレイにクジラのアイコンが表示されるまで待つ
3. エラーが表示されている場合は、Docker Desktopを再起動

### データベース接続エラー
- Dockerを使う場合: `.env`ファイルの`DB_HOST=db`を確認
- ローカル起動の場合: `.env`ファイルの`DB_HOST=localhost`を確認し、PostgreSQLが起動していることを確認

### ポートが既に使用されている
- ポート8000が既に使用されている場合は、`python manage.py runserver 8001`のように別のポートを指定

