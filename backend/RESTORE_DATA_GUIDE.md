# データ復元ガイド

## 現在の状況

- ローカルデータベース: ユーザー3人、投稿5件
- バックアップファイル: ローカルには見つかりませんでした
- 本番サーバー（160.251.168.144）にバックアップがある可能性が高いです

## 復元手順

### ステップ1: 本番サーバーにアクセス

#### 方法A: VNCコンソール経由（推奨）

1. ConoHaの管理画面にログイン
2. サーバー一覧から該当サーバー（160.251.168.144）を選択
3. 「VNCコンソール」または「コンソール」をクリック
4. `root`ユーザーでログイン

#### 方法B: SSH接続（可能な場合）

```bash
ssh app@160.251.168.144
# または
ssh root@160.251.168.144
```

### ステップ2: バックアップファイルを探す

本番サーバーで以下のコマンドを実行：

```bash
# appユーザーで実行
cd ~/toybox/backend

# バックアップファイルを探す
find ~/toybox -name "*.sql" -o -name "*.dump" -o -name "*backup*" 2>/dev/null

# 今日の14:00頃のバックアップを探す（2025-12-17 14:00頃）
ls -lah ~/toybox/backend/*.sql 2>/dev/null
ls -lah ~/toybox/backend/backup*.sql 2>/dev/null
ls -lah ~/toybox/backend/*20251217*.sql 2>/dev/null
```

### ステップ3: バックアップファイルをローカルにダウンロード

見つかったバックアップファイルをローカルにダウンロード：

#### SCPを使用（SSH接続可能な場合）

```powershell
# PowerShellで実行
scp app@160.251.168.144:~/toybox/backend/backup_20251217_140000.sql C:\github\toybox\backend\
```

#### VNCコンソール経由の場合

1. バックアップファイルの内容をコピー
2. ローカルに新しいファイルとして保存: `C:\github\toybox\backend\backup_restore.sql`

### ステップ4: ローカルデータベースを復元

```powershell
# backendディレクトリに移動
cd C:\github\toybox\backend

# 現在のデータベースをバックアップ（念のため）
docker compose exec -T db pg_dump -U postgres toybox > backup_before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql

# データベースを削除して再作成
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS toybox;"
docker compose exec db psql -U postgres -c "CREATE DATABASE toybox;"

# バックアップから復元
Get-Content backup_restore.sql | docker compose exec -T db psql -U postgres toybox
```

### ステップ5: 復元の確認

```powershell
# データの件数を確認
docker compose exec db psql -U postgres -d toybox -c "SELECT 'users' as table_name, COUNT(*) as count FROM users UNION ALL SELECT 'submissions', COUNT(*) FROM submissions UNION ALL SELECT 'reactions', COUNT(*) FROM reactions;"
```

## 注意事項

- **復元前に必ず現在のデータベースをバックアップしてください**
- 復元はデータベース全体を上書きします
- メディアファイル（画像・動画）も必要に応じて復元してください

## メディアファイルの復元

投稿画像や動画も復元する必要がある場合：

```bash
# 本番サーバーで実行
cd ~/toybox/backend
tar -czf uploads_backup_20251217_140000.tar.gz public/uploads/

# ローカルにダウンロード（SCP使用）
scp app@160.251.168.144:~/toybox/backend/uploads_backup_20251217_140000.tar.gz C:\github\toybox\backend\

# ローカルで展開
cd C:\github\toybox\backend
tar -xzf uploads_backup_20251217_140000.tar.gz
```

## トラブルシューティング

### バックアップファイルが見つからない場合

1. 本番サーバーのDockerボリュームを確認：
   ```bash
   docker volume ls
   docker volume inspect toybox_postgres_data
   ```

2. 本番サーバーから直接データベースをダンプ：
   ```bash
   docker compose exec -T db pg_dump -U postgres toybox > backup_from_prod_$(date +%Y%m%d_%H%M%S).sql
   ```

### 復元時にエラーが発生する場合

- エラーメッセージを確認
- マイグレーションが必要な場合は実行：
  ```powershell
  cd C:\github\toybox\backend
  docker compose exec web python manage.py migrate
  ```

