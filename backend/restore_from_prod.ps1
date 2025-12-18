# 本番サーバーからデータベースを復元するスクリプト
# 使用方法: .\restore_from_prod.ps1

Write-Host "=== 本番サーバーからデータベースを復元 ===" -ForegroundColor Cyan

# ステップ1: 本番サーバーからバックアップを取得
Write-Host "`nステップ1: 本番サーバーからバックアップを取得" -ForegroundColor Yellow
Write-Host "以下のコマンドを本番サーバー（VNCコンソール経由）で実行してください:" -ForegroundColor White
Write-Host ""
Write-Host "  cd ~/toybox/backend" -ForegroundColor Green
Write-Host "  docker compose exec -T db pg_dump -U postgres toybox > backup_restore.sql" -ForegroundColor Green
Write-Host ""
Write-Host "その後、backup_restore.sqlファイルをローカルの C:\github\toybox\backend\ にコピーしてください" -ForegroundColor White
Write-Host ""

$backupFile = "C:\github\toybox\backend\backup_restore.sql"
if (-not (Test-Path $backupFile)) {
    Write-Host "エラー: backup_restore.sql が見つかりません" -ForegroundColor Red
    Write-Host "本番サーバーからバックアップファイルを取得して、$backupFile に配置してください" -ForegroundColor Yellow
    exit 1
}

Write-Host "バックアップファイルが見つかりました: $backupFile" -ForegroundColor Green

# ステップ2: 現在のデータベースをバックアップ
Write-Host "`nステップ2: 現在のデータベースをバックアップ" -ForegroundColor Yellow
$currentBackup = "backup_before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
Write-Host "現在のデータベースをバックアップ中: $currentBackup" -ForegroundColor White
docker compose exec -T db pg_dump -U postgres toybox > $currentBackup
if ($LASTEXITCODE -eq 0) {
    Write-Host "バックアップ完了: $currentBackup" -ForegroundColor Green
} else {
    Write-Host "エラー: バックアップに失敗しました" -ForegroundColor Red
    exit 1
}

# ステップ3: データベースを削除して再作成
Write-Host "`nステップ3: データベースを削除して再作成" -ForegroundColor Yellow
Write-Host "警告: これにより現在のデータベースが削除されます" -ForegroundColor Red
$confirm = Read-Host "続行しますか? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "キャンセルしました" -ForegroundColor Yellow
    exit 0
}

Write-Host "データベースを削除中..." -ForegroundColor White
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS toybox;"
if ($LASTEXITCODE -ne 0) {
    Write-Host "エラー: データベースの削除に失敗しました" -ForegroundColor Red
    exit 1
}

Write-Host "データベースを再作成中..." -ForegroundColor White
docker compose exec db psql -U postgres -c "CREATE DATABASE toybox;"
if ($LASTEXITCODE -ne 0) {
    Write-Host "エラー: データベースの作成に失敗しました" -ForegroundColor Red
    exit 1
}

# ステップ4: バックアップから復元
Write-Host "`nステップ4: バックアップから復元" -ForegroundColor Yellow
Write-Host "バックアップファイルを復元中..." -ForegroundColor White
Get-Content $backupFile | docker compose exec -T db psql -U postgres toybox
if ($LASTEXITCODE -eq 0) {
    Write-Host "復元完了!" -ForegroundColor Green
} else {
    Write-Host "エラー: 復元に失敗しました" -ForegroundColor Red
    Write-Host "バックアップファイル ($currentBackup) から手動で復元してください" -ForegroundColor Yellow
    exit 1
}

# ステップ5: 復元の確認
Write-Host "`nステップ5: 復元の確認" -ForegroundColor Yellow
Write-Host "データの件数を確認中..." -ForegroundColor White
docker compose exec db psql -U postgres -d toybox -c "SELECT 'users' as table_name, COUNT(*) as count FROM users UNION ALL SELECT 'submissions', COUNT(*) FROM submissions UNION ALL SELECT 'reactions', COUNT(*) FROM reactions UNION ALL SELECT 'user_meta', COUNT(*) FROM user_meta;"

Write-Host "`n復元が完了しました!" -ForegroundColor Green
Write-Host "マイグレーションが必要な場合は実行してください:" -ForegroundColor Yellow
Write-Host "  docker compose exec web python manage.py migrate" -ForegroundColor White


