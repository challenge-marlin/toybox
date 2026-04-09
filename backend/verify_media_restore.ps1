# メディアボリュームリストア検証スクリプト
# リストア後にメディアファイルとデータベースの整合性を確認します

param(
    [Parameter(Mandatory=$false)]
    [switch]$Detailed
)

$ErrorActionPreference = "Stop"

# 設定
$VOLUME_NAME = "backend_media_volume"

# 色設定
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-MediaFile {
    param(
        [string]$FilePath
    )
    
    if (!$FilePath) {
        return $false
    }
    
    # URLパスをファイルシステムパスに変換（例: /media/uploads/... -> uploads/...）
    $relativePath = $FilePath -replace '^/media/', '' -replace '^media/', ''
    
    $result = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "test -f /data/$relativePath && echo 'exists' || echo 'missing'"
    return $result.Trim() -eq "exists"
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "メディアボリューム検証" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# 1. ボリューム基本情報
Write-ColorOutput "📊 ボリューム基本情報" "Yellow"
Write-Host ""

$fileCount = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type f | wc -l"
$dirCount = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type d | wc -l"
$totalSize = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "du -sh /data"

Write-Host "ファイル数: $fileCount"
Write-Host "ディレクトリ数: $dirCount"
Write-Host "総サイズ: $totalSize"

# 2. ディレクトリ構造
Write-Host ""
Write-ColorOutput "📁 ディレクトリ構造" "Yellow"
docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type d | sort | head -20"

# 3. ファイル種別の集計
Write-Host ""
Write-ColorOutput "📄 ファイル種別" "Yellow"

$extensions = @{}
$fileList = docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type f -name '*.*'"
$fileList -split "`n" | ForEach-Object {
    if ($_ -match '\.([^.]+)$') {
        $ext = $matches[1].ToLower()
        if (!$extensions.ContainsKey($ext)) {
            $extensions[$ext] = 0
        }
        $extensions[$ext]++
    }
}

$extensions.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
    Write-Host "  .$($_.Key): $($_.Value) ファイル"
}

# 4. 最新のファイル
Write-Host ""
Write-ColorOutput "🕐 最新のファイル（更新日時順）" "Yellow"
docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -type f -printf '%T+ %p\n' | sort -r | head -10" 2>$null

if ($LASTEXITCODE -ne 0) {
    # Alpine Linuxではfindの-printfが使えない場合
    docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "ls -lt \$(find /data -type f) | head -10"
}

# 5. データベースとの整合性チェック
Write-Host ""
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "データベース整合性チェック" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-Host ""

# Dockerコンテナが起動しているか確認
$webContainer = docker ps --filter "name=backend-web" --format "{{.Names}}" 2>$null
if (!$webContainer) {
    Write-ColorOutput "⚠️ Webコンテナが起動していません" "Yellow"
    Write-Host "docker compose up -d を実行してください"
} else {
    Write-ColorOutput "✅ Webコンテナが起動しています" "Green"
    
    # データベース接続確認
    $dbContainer = docker ps --filter "name=backend-db" --format "{{.Names}}" 2>$null
    if (!$dbContainer) {
        Write-ColorOutput "⚠️ DBコンテナが起動していません" "Yellow"
    } else {
        Write-ColorOutput "✅ DBコンテナが起動しています" "Green"
        
        Write-Host ""
        Write-ColorOutput "🔍 ユーザープロファイル画像をチェック中..." "Yellow"
        
        # ユーザープロファイル画像のチェック
        $profileQuery = @"
SELECT u.id, u.username, um.profile_image
FROM users_user u
LEFT JOIN users_usermeta um ON u.id = um.user_id
WHERE um.profile_image IS NOT NULL AND um.profile_image != ''
LIMIT 10;
"@
        
        $profiles = docker compose exec -T db psql -U postgres -d toybox -t -c $profileQuery 2>$null
        
        if ($profiles) {
            $profileLines = $profiles -split "`n" | Where-Object { $_.Trim() -ne "" }
            $missingProfiles = 0
            $existingProfiles = 0
            
            foreach ($line in $profileLines) {
                $parts = $line -split "\|"
                if ($parts.Length -ge 3) {
                    $userId = $parts[0].Trim()
                    $username = $parts[1].Trim()
                    $imagePath = $parts[2].Trim()
                    
                    if ($imagePath) {
                        $exists = Test-MediaFile $imagePath
                        if ($exists) {
                            $existingProfiles++
                            if ($Detailed) {
                                Write-ColorOutput "  ✅ ユーザー $username : $imagePath" "Green"
                            }
                        } else {
                            $missingProfiles++
                            Write-ColorOutput "  ❌ ユーザー $username : $imagePath (見つかりません)" "Red"
                        }
                    }
                }
            }
            
            Write-Host ""
            Write-Host "プロファイル画像の存在: $existingProfiles / $($existingProfiles + $missingProfiles)"
            if ($missingProfiles -eq 0) {
                Write-ColorOutput "✅ すべてのプロファイル画像が存在します" "Green"
            } else {
                Write-ColorOutput "⚠️ $missingProfiles 個のプロファイル画像が見つかりません" "Yellow"
            }
        }
        
        Write-Host ""
        Write-ColorOutput "🎴 カード画像をチェック中..." "Yellow"
        
        # カード画像のチェック
        $cardQuery = @"
SELECT id, name, image, image_url
FROM gamification_card
WHERE (image IS NOT NULL AND image != '') OR (image_url IS NOT NULL AND image_url != '')
LIMIT 10;
"@
        
        $cards = docker compose exec -T db psql -U postgres -d toybox -t -c $cardQuery 2>$null
        
        if ($cards) {
            $cardLines = $cards -split "`n" | Where-Object { $_.Trim() -ne "" }
            $missingCards = 0
            $existingCards = 0
            
            foreach ($line in $cardLines) {
                $parts = $line -split "\|"
                if ($parts.Length -ge 4) {
                    $cardId = $parts[0].Trim()
                    $cardName = $parts[1].Trim()
                    $imagePath = $parts[2].Trim()
                    $imageUrl = $parts[3].Trim()
                    
                    $pathToCheck = if ($imagePath) { $imagePath } else { $imageUrl }
                    
                    if ($pathToCheck) {
                        $exists = Test-MediaFile $pathToCheck
                        if ($exists) {
                            $existingCards++
                            if ($Detailed) {
                                Write-ColorOutput "  ✅ カード $cardName : $pathToCheck" "Green"
                            }
                        } else {
                            $missingCards++
                            Write-ColorOutput "  ⚠️ カード $cardName : $pathToCheck (見つかりません)" "Yellow"
                        }
                    }
                }
            }
            
            Write-Host ""
            Write-Host "カード画像の存在: $existingCards / $($existingCards + $missingCards)"
            if ($missingCards -eq 0) {
                Write-ColorOutput "✅ すべてのカード画像が存在します" "Green"
            } else {
                Write-ColorOutput "⚠️ $missingCards 個のカード画像が見つかりません" "Yellow"
                Write-ColorOutput "   ※カード画像は外部URLの場合もあります" "Gray"
            }
        }
    }
}

# 6. サンプルファイルの表示
if ($Detailed) {
    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "サンプルファイル詳細" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""
    
    Write-ColorOutput "📸 画像ファイル（JPG）" "Yellow"
    docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -name '*.jpg' -o -name '*.jpeg' | head -5"
    
    Write-Host ""
    Write-ColorOutput "📸 画像ファイル（PNG）" "Yellow"
    docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -name '*.png' | head -5"
    
    Write-Host ""
    Write-ColorOutput "📸 画像ファイル（GIF）" "Yellow"
    docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -name '*.gif' | head -5"
    
    Write-Host ""
    Write-ColorOutput "📸 画像ファイル（WEBP）" "Yellow"
    docker run --rm -v ${VOLUME_NAME}:/data alpine sh -c "find /data -name '*.webp' | head -5"
}

# 完了
Write-Host ""
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "検証完了" "Green"
Write-ColorOutput "========================================" "Green"
Write-Host ""
Write-ColorOutput "次のステップ:" "White"
Write-ColorOutput "1. ブラウザで http://localhost:8000 にアクセス" "White"
Write-ColorOutput "2. ログインしてプロファイル画像を確認" "White"
Write-ColorOutput "3. ガチャページでカード画像を確認" "White"
Write-ColorOutput "4. 開発者ツール（F12）で404エラーがないか確認" "White"
Write-Host ""

if ($Detailed) {
    Write-ColorOutput "詳細情報を表示しました" "Cyan"
} else {
    Write-ColorOutput "詳細情報を表示するには -Detailed オプションを使用してください" "Gray"
}
