# カードマスタデータをロードするPowerShellスクリプト

Write-Host "カードマスタデータをロードします..." -ForegroundColor Green

# 仮想環境をアクティベート
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "仮想環境をアクティベート中..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "警告: 仮想環境が見つかりません。pyランチャーを使用します。" -ForegroundColor Yellow
}

# カードマスタデータをロード
Write-Host "カードマスタデータをロード中..." -ForegroundColor Yellow
try {
    python manage.py load_card_master
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nカードマスタデータのロードが完了しました！" -ForegroundColor Green
    } else {
        Write-Host "`nエラーが発生しました。エラーメッセージを確認してください。" -ForegroundColor Red
    }
} catch {
    Write-Host "`nエラーが発生しました: $_" -ForegroundColor Red
    Write-Host "`npyランチャーで再試行します..." -ForegroundColor Yellow
    py manage.py load_card_master
}

Write-Host "`n完了しました。" -ForegroundColor Green
