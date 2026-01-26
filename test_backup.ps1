# TOYBOXバックアップテストスクリプト（ローカル版）

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "TOYBOXバックアップシステム ローカルテスト" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$DATE = Get-Date -Format "yyyyMMdd_HHmmss"
$DATE_SHORT = Get-Date -Format "yyyyMMdd"
$BACKUP_ROOT = "C:\backup\toybox"

# ディレクトリ作成
Write-Host "[1/5] バックアップディレクトリを作成中..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$BACKUP_ROOT\database" -Force | Out-Null
New-Item -ItemType Directory -Path "$BACKUP_ROOT\volumes" -Force | Out-Null
New-Item -ItemType Directory -Path "$BACKUP_ROOT\volumes-incremental" -Force | Out-Null
Write-Host "✅ 完了" -ForegroundColor Green
Write-Host ""

# PostgreSQLダンプ
Write-Host "[2/5] PostgreSQLダンプを実行中..." -ForegroundColor Yellow
docker exec backend-db-1 pg_dump -U postgres toybox | Out-File -Encoding utf8 "$BACKUP_ROOT\database\toybox_$DATE.sql"
if (Test-Path "$BACKUP_ROOT\database\toybox_$DATE.sql") {
    $size = (Get-Item "$BACKUP_ROOT\database\toybox_$DATE.sql").Length
    Write-Host "✅ 完了 (サイズ: $([math]::Round($size/1KB, 2)) KB)" -ForegroundColor Green
} else {
    Write-Host "❌ 失敗" -ForegroundColor Red
}
Write-Host ""

# Dockerボリューム完全バックアップ
Write-Host "[3/5] Dockerボリューム完全バックアップを実行中..." -ForegroundColor Yellow
Write-Host "  - PostgreSQLボリューム..." -ForegroundColor Gray
docker run --rm `
  -v backend_postgres_data:/data:ro `
  -v ${BACKUP_ROOT}\volumes:/backup `
  alpine tar czf /backup/postgres_data_$DATE_SHORT.tar.gz /data 2>$null

Write-Host "  - メディアボリューム..." -ForegroundColor Gray
docker run --rm `
  -v backend_media_volume:/data:ro `
  -v ${BACKUP_ROOT}\volumes:/backup `
  alpine tar czf /backup/media_volume_$DATE_SHORT.tar.gz /data 2>$null

if ((Test-Path "$BACKUP_ROOT\volumes\postgres_data_$DATE_SHORT.tar.gz") -and 
    (Test-Path "$BACKUP_ROOT\volumes\media_volume_$DATE_SHORT.tar.gz")) {
    $size1 = (Get-Item "$BACKUP_ROOT\volumes\postgres_data_$DATE_SHORT.tar.gz").Length
    $size2 = (Get-Item "$BACKUP_ROOT\volumes\media_volume_$DATE_SHORT.tar.gz").Length
    Write-Host "✅ 完了 (PostgreSQL: $([math]::Round($size1/1MB, 2)) MB, Media: $([math]::Round($size2/1MB, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ 失敗" -ForegroundColor Red
}
Write-Host ""

# Dockerボリューム差分バックアップ
Write-Host "[4/5] Dockerボリューム差分バックアップを実行中..." -ForegroundColor Yellow
$BASE_DIR = "$BACKUP_ROOT\volumes-incremental\base_$DATE_SHORT"
$INCR_DIR = "$BACKUP_ROOT\volumes-incremental\incr_$DATE_SHORT"
New-Item -ItemType Directory -Path $BASE_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $INCR_DIR -Force | Out-Null

Write-Host "  - ベースバックアップ作成..." -ForegroundColor Gray
docker run --rm `
  -v backend_postgres_data:/source:ro `
  -v ${BASE_DIR}:/backup `
  alpine sh -c "cp -a /source /backup/postgres_data" 2>$null

docker run --rm `
  -v backend_media_volume:/source:ro `
  -v ${BASE_DIR}:/backup `
  alpine sh -c "cp -a /source /backup/media_volume" 2>$null

Write-Host "  - 差分バックアップ作成..." -ForegroundColor Gray
docker run --rm `
  -v backend_postgres_data:/source:ro `
  -v ${BASE_DIR}\postgres_data:/base:ro `
  -v ${INCR_DIR}:/backup `
  alpine sh -c "apk add --no-cache rsync > /dev/null 2>&1 && rsync -a --delete --link-dest=/base /source/ /backup/postgres_data/" 2>$null

docker run --rm `
  -v backend_media_volume:/source:ro `
  -v ${BASE_DIR}\media_volume:/base:ro `
  -v ${INCR_DIR}:/backup `
  alpine sh -c "apk add --no-cache rsync > /dev/null 2>&1 && rsync -a --delete --link-dest=/base /source/ /backup/media_volume/" 2>$null

if ((Test-Path "$BASE_DIR\postgres_data") -and (Test-Path "$INCR_DIR\postgres_data")) {
    Write-Host "✅ 完了" -ForegroundColor Green
} else {
    Write-Host "❌ 失敗" -ForegroundColor Red
}
Write-Host ""

# サマリー
Write-Host "[5/5] テスト結果サマリー" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📂 バックアップファイル一覧:" -ForegroundColor White
Write-Host ""
Write-Host "【PostgreSQLダンプ】" -ForegroundColor Cyan
Get-ChildItem "$BACKUP_ROOT\database" -Recurse | ForEach-Object {
    Write-Host "  $($_.Name) - $([math]::Round($_.Length/1KB, 2)) KB" -ForegroundColor Gray
}
Write-Host ""
Write-Host "【ボリューム完全バックアップ】" -ForegroundColor Cyan
Get-ChildItem "$BACKUP_ROOT\volumes" -Recurse -File | ForEach-Object {
    Write-Host "  $($_.Name) - $([math]::Round($_.Length/1MB, 2)) MB" -ForegroundColor Gray
}
Write-Host ""
Write-Host "【ボリューム差分バックアップ】" -ForegroundColor Cyan
Get-ChildItem "$BACKUP_ROOT\volumes-incremental" -Directory | ForEach-Object {
    Write-Host "  $($_.Name)" -ForegroundColor Gray
}
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ すべてのテストが完了しました！" -ForegroundColor Green
Write-Host ""
Write-Host "バックアップファイルの場所: C:\backup\toybox\" -ForegroundColor White
Write-Host ""
