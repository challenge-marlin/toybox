# データベースをリセットするスクリプト（UTF-8文字セットで再作成）
# 使用方法: .\reset_database.ps1
# 
# 警告: このスクリプトは既存のデータベースを削除します

$ErrorActionPreference = "Stop"

Write-Host "=== データベースをリセット ===" -ForegroundColor Cyan
Write-Host ""

# 警告を表示
Write-Host "警告: このスクリプトは既存のデータベース 'toybox' を削除します" -ForegroundColor Red
Write-Host ""

# 現在のデータベースをバックアップするか確認
$backup = Read-Host "現在のデータベースをバックアップしますか? (yes/no)"
if ($backup -eq "yes") {
    $backupFile = "backup_before_reset_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    Write-Host "データベースをバックアップ中: $backupFile" -ForegroundColor Yellow
    
    try {
        docker compose exec -T db pg_dump -U postgres --encoding=UTF8 toybox > $backupFile
        if ($LASTEXITCODE -eq 0) {
            Write-Host "バックアップ完了: $backupFile" -ForegroundColor Green
        } else {
            Write-Host "警告: バックアップに失敗しましたが、続行します" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "警告: バックアップに失敗しましたが、続行します" -ForegroundColor Yellow
    }
    Write-Host ""
}

# 確認
$confirm = Read-Host "データベースを削除して再作成しますか? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "キャンセルしました" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "データベースを削除中..." -ForegroundColor White
try {
    docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS toybox;" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "データベースの削除が完了しました" -ForegroundColor Green
    } else {
        Write-Host "警告: データベースの削除に失敗しました" -ForegroundColor Yellow
    }
} catch {
    Write-Host "警告: データベースの削除に失敗しました: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "データベースを再作成中（UTF-8文字セット指定）..." -ForegroundColor White
try {
    docker compose exec db psql -U postgres -c "CREATE DATABASE toybox WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;" | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "データベースの作成が完了しました" -ForegroundColor Green
    } else {
        Write-Host "エラー: データベースの作成に失敗しました" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "エラー: データベースの作成に失敗しました: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "データベースの文字セットを確認中..." -ForegroundColor White
docker compose exec db psql -U postgres -d toybox -c "SHOW server_encoding;"

Write-Host ""
Write-Host "=== データベースのリセットが完了しました ===" -ForegroundColor Green
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Yellow
Write-Host "1. SQLファイルをリストアしてください" -ForegroundColor White
Write-Host "2. 例: .\restore_from_prod_complete.ps1" -ForegroundColor White
Write-Host ""
