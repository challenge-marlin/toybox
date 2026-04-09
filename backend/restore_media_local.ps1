# メディアボリュームローカルリストアスクリプト
# ローカル環境でPowerShellから実行してください

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# 設定
$VOLUME_NAME = "backend_media_volume"
$BACKUP_DIR = "C:\github\toybox\backend\media_backups"
$CURRENT_DIR = Get-Location

# 色設定
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "メディアボリュームリストア" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# バックアップファイルのパスを解決
if (!(Test-Path $BackupFile)) {
    $BackupFile = Join-Path $BACKUP_DIR $BackupFile
}

if (!(Test-Path $BackupFile)) {
    Write-ColorOutput "バックアップファイルが見つかりません: $BackupFile" "Red"
    exit 1
}

$BackupFile = Resolve-Path $BackupFile
Write-ColorOutput "バックアップファイル: $BackupFile" "White"

# ハッシュ値チェック
$HashFile = "$BackupFile.sha256"
if (Test-Path $HashFile) {
    Write-ColorOutput "ハッシュ値を検証中..." "Yellow"
    $expectedHash = (Get-Content $HashFile).Split(" ")[0]
    $actualHash = (Get-FileHash $BackupFile -Algorithm SHA256).Hash.ToLower()
    
    if ($expectedHash -eq $actualHash) {
        Write-ColorOutput "ハッシュ値が一致しました" "Green"
    } else {
        Write-ColorOutput "ハッシュ値が一致しません" "Red"
        if (!$Force) {
            Write-ColorOutput "リストアを中止します。強制実行する場合は -Force オプションを使用してください。" "Yellow"
            exit 1
        }
    }
} else {
    Write-ColorOutput "ハッシュファイルが見つかりません" "Yellow"
}

# 現在の状態を確認
Write-Host ""
Write-ColorOutput "現在のメディアボリューム状態を確認中..." "Yellow"
$currentFileCount = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type f 2>/dev/null | wc -l"
Write-ColorOutput "現在のファイル数: $currentFileCount" "White"

# 確認プロンプト
if (!$Force) {
    Write-Host ""
    Write-ColorOutput "警告: 現在のメディアボリュームの内容は削除されます" "Yellow"
    $confirmation = Read-Host "続行しますか？ (yes/no)"
    if ($confirmation -ne "yes") {
        Write-ColorOutput "リストアをキャンセルしました" "Yellow"
        exit 0
    }
}

# 現在のメディアボリュームをバックアップ（念のため）
if (!$SkipBackup -and $currentFileCount -gt 0) {
    Write-Host ""
    Write-ColorOutput "現在のメディアボリュームをバックアップ中..." "Yellow"
    $backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
    $localBackupFile = "$BACKUP_DIR\local_media_before_restore_$backupDate.tar.gz"
    
    if (!(Test-Path $BACKUP_DIR)) {
        New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    }
    
    docker run --rm `
      -v ${VOLUME_NAME}:/source:ro `
      -v ${BACKUP_DIR}:/backup `
      alpine tar czf /backup/local_media_before_restore_$backupDate.tar.gz -C /source .
    
    if (Test-Path $localBackupFile) {
        $backupSize = (Get-Item $localBackupFile).Length / 1MB
        Write-ColorOutput "バックアップ完了: $([math]::Round($backupSize, 2)) MB" "Green"
    }
}

# メディアボリュームをクリア
Write-Host ""
Write-ColorOutput "メディアボリュームをクリア中..." "Yellow"
docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "rm -rf /data/*"
Write-ColorOutput "クリア完了" "Green"

# リストア実行
Write-Host ""
Write-ColorOutput "バックアップからリストア中..." "Yellow"

docker run --rm `
  -v ${VOLUME_NAME}:/target `
  -v ${BackupFile}:/backup.tar.gz:ro `
  alpine tar xzf /backup.tar.gz -C /target

Write-ColorOutput "リストア完了" "Green"

# リストア結果の検証
Write-Host ""
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "検証" "Cyan"
Write-ColorOutput "========================================" "Cyan"

# ファイル数を確認
Write-ColorOutput "ファイル数を確認中..." "Yellow"
$restoredCount = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type f | wc -l"
Write-ColorOutput "リストアされたファイル数: $restoredCount" "Cyan"

# バックアップ情報ファイルがあれば比較
$infoFile = $BackupFile -replace '\.tar\.gz$', ''
$infoFile = $infoFile -replace 'media_volume_', 'media_backup_' 
$infoFile = "$infoFile" + "_info.txt"

if (Test-Path $infoFile) {
    $infoContent = Get-Content $infoFile
    $originalCount = ($infoContent | Where-Object { $_ -match "ファイル数:" }).Split(":")[1].Trim()
    Write-ColorOutput "元のファイル数: $originalCount" "Cyan"
    
    if ($restoredCount -eq $originalCount) {
        Write-ColorOutput "ファイル数が一致しました" "Green"
    } else {
        Write-ColorOutput "ファイル数が異なります" "Yellow"
    }
} else {
    Write-ColorOutput "バックアップ情報ファイルが見つかりません" "Yellow"
}

# ディレクトリ構造を確認
Write-Host ""
Write-ColorOutput "ディレクトリ構造:" "Yellow"
docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type d | head -10"

# サンプルファイルを確認
Write-Host ""
Write-ColorOutput "サンプルファイル（最初の10件）:" "Yellow"
docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type f | head -10"

# 総サイズを確認
Write-Host ""
Write-ColorOutput "総サイズ:" "Yellow"
docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "du -sh /data"

# 完了メッセージ
Write-Host ""
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "リストアが完了しました" "Green"
Write-ColorOutput "========================================" "Green"
Write-Host ""
Write-ColorOutput "次のステップ:" "White"
Write-ColorOutput "1. Dockerコンテナを起動:" "White"
Write-Host "   docker compose up -d"
Write-ColorOutput "2. Webブラウザで画像表示を確認:" "White"
Write-Host "   http://localhost:8000"
Write-ColorOutput "3. プロファイル画像、カード画像が正しく表示されるか確認" "White"
Write-Host ""
