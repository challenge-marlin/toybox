# TOYBOXバックアップ復元テストスクリプト

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "TOYBOXバックアップ復元テスト" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# バックアップファイルのパスを指定
$BACKUP_FILE = Read-Host "バックアップファイルのパスを入力してください（例: C:\backup\toybox-restore-test\toybox_20260126_170000.sql.gz）"

# ファイルの存在確認
if (-not (Test-Path $BACKUP_FILE)) {
    Write-Host "❌ エラー: バックアップファイルが見つかりません" -ForegroundColor Red
    Write-Host "   パス: $BACKUP_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "✅ バックアップファイルを確認しました" -ForegroundColor Green
$size = (Get-Item $BACKUP_FILE).Length
Write-Host "   ファイルサイズ: $([math]::Round($size/1KB, 2)) KB" -ForegroundColor Gray
Write-Host ""

# 復元前のデータを確認
Write-Host "[1/4] 復元前のデータを確認中..." -ForegroundColor Yellow
Write-Host ""

try {
    $userCount = docker exec backend-db-1 psql -U postgres toybox -t -c "SELECT COUNT(*) FROM users;" 2>$null | ForEach-Object { $_.Trim() }
    $postCount = docker exec backend-db-1 psql -U postgres toybox -t -c "SELECT COUNT(*) FROM posts;" 2>$null | ForEach-Object { $_.Trim() }
    
    Write-Host "  現在のユーザー数: $userCount" -ForegroundColor Gray
    Write-Host "  現在の投稿数: $postCount" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "  ⚠️ データベースが存在しない可能性があります" -ForegroundColor Yellow
    Write-Host ""
}

# 確認メッセージ
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "【警告】" -ForegroundColor Red
Write-Host "この操作は現在のデータベースを上書きします。" -ForegroundColor Yellow
Write-Host "ローカル環境でのテストであることを確認してください。" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "復元を実行しますか？ (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "復元をキャンセルしました" -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# 復元を実行
Write-Host "[2/4] バックアップから復元中..." -ForegroundColor Yellow
Write-Host "  ※エラーメッセージが表示されることがありますが、正常です" -ForegroundColor Gray
Write-Host ""

if ($BACKUP_FILE -like "*.gz") {
    # 圧縮ファイルの場合
    Write-Host "  圧縮ファイルを解凍しながら復元中..." -ForegroundColor Gray
    
    # 一時的に解凍
    $tempFile = $BACKUP_FILE -replace "\.gz$", ""
    
    try {
        # 7-Zipで解凍
        if (Test-Path "C:\Program Files\7-Zip\7z.exe") {
            & "C:\Program Files\7-Zip\7z.exe" e $BACKUP_FILE "-o$(Split-Path $tempFile)" -y | Out-Null
        } else {
            Write-Host "❌ 7-Zipが見つかりません。手動で解凍してください。" -ForegroundColor Red
            exit 1
        }
        
        # 復元
        Get-Content $tempFile | docker exec -i backend-db-1 psql -U postgres toybox 2>&1 | Out-Null
        
        # 一時ファイル削除
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        
        Write-Host "✅ 復元完了" -ForegroundColor Green
    } catch {
        Write-Host "❌ 復元に失敗しました" -ForegroundColor Red
        Write-Host "   エラー: $_" -ForegroundColor Red
        exit 1
    }
} else {
    # 非圧縮ファイルの場合
    Write-Host "  復元中..." -ForegroundColor Gray
    
    try {
        Get-Content $BACKUP_FILE | docker exec -i backend-db-1 psql -U postgres toybox 2>&1 | Out-Null
        Write-Host "✅ 復元完了" -ForegroundColor Green
    } catch {
        Write-Host "❌ 復元に失敗しました" -ForegroundColor Red
        Write-Host "   エラー: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# 復元後のデータを確認
Write-Host "[3/4] 復元後のデータを確認中..." -ForegroundColor Yellow
Write-Host ""

try {
    $userCountAfter = docker exec backend-db-1 psql -U postgres toybox -t -c "SELECT COUNT(*) FROM users;" 2>$null | ForEach-Object { $_.Trim() }
    $postCountAfter = docker exec backend-db-1 psql -U postgres toybox -t -c "SELECT COUNT(*) FROM posts;" 2>$null | ForEach-Object { $_.Trim() }
    
    Write-Host "  復元後のユーザー数: $userCountAfter" -ForegroundColor Gray
    Write-Host "  復元後の投稿数: $postCountAfter" -ForegroundColor Gray
    Write-Host ""
    
    # 変化を表示
    if ($userCount -ne $null -and $userCountAfter -ne $null) {
        if ($userCount -ne $userCountAfter) {
            Write-Host "  📊 ユーザー数が変化しました: $userCount → $userCountAfter" -ForegroundColor Cyan
        } else {
            Write-Host "  📊 ユーザー数は変化していません: $userCount" -ForegroundColor Gray
        }
    }
    
    if ($postCount -ne $null -and $postCountAfter -ne $null) {
        if ($postCount -ne $postCountAfter) {
            Write-Host "  📊 投稿数が変化しました: $postCount → $postCountAfter" -ForegroundColor Cyan
        } else {
            Write-Host "  📊 投稿数は変化していません: $postCount" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
} catch {
    Write-Host "  ⚠️ データの確認に失敗しました" -ForegroundColor Yellow
    Write-Host ""
}

# 最新のユーザーを表示
Write-Host "[4/4] 復元データのサンプルを表示..." -ForegroundColor Yellow
Write-Host ""
Write-Host "【最新のユーザー5件】" -ForegroundColor Cyan
docker exec backend-db-1 psql -U postgres toybox -c "SELECT id, username, email FROM users ORDER BY id DESC LIMIT 5;" 2>$null
Write-Host ""

# まとめ
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ 復元テストが完了しました！" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "【次の確認】" -ForegroundColor Yellow
Write-Host "  1. ブラウザで http://localhost:8000/admin/ にアクセス" -ForegroundColor Gray
Write-Host "  2. データが正常に表示されるか確認" -ForegroundColor Gray
Write-Host "  3. エラーが出ていないか確認" -ForegroundColor Gray
Write-Host ""
