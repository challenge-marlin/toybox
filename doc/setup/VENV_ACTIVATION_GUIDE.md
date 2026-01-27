# 仮想環境のアクティベート手順（Windows PowerShell）

## 問題

PowerShellで`.\venv\Scripts\Activate.ps1`を実行すると、以下のエラーが発生する場合があります：

```
.\venv\Scripts\Activate.ps1 : 用語 '.\venv\Scripts\Activate.ps1' は、コマンドレット、関数、スクリプト ファイル、または操作可能なプログラムの名前として認識されません。
```

## 原因

現在のディレクトリが`backend`ディレクトリではない場合に発生します。

## 解決方法

### 方法1: 正しいディレクトリに移動してからアクティベート

```powershell
# プロジェクトのルートディレクトリから
cd backend
.\venv\Scripts\Activate.ps1
```

### 方法2: 絶対パスまたは相対パスを指定

```powershell
# プロジェクトのルートディレクトリから
.\backend\venv\Scripts\Activate.ps1
```

### 方法3: 実行ポリシーのエラーが出る場合

PowerShellの実行ポリシーが制限されている場合、以下のコマンドを実行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

その後、再度アクティベート：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

## 確認方法

仮想環境が正しくアクティベートされているか確認：

```powershell
# Pythonのバージョンを確認
python --version

# 仮想環境がアクティベートされている場合、プロンプトの前に (venv) が表示されます
# 例: (venv) PS C:\github\toybox\backend>
```

## よくある問題と解決方法

### 問題1: 実行ポリシーエラー

**エラーメッセージ**:
```
このシステムではスクリプトの実行が無効になっているため、ファイルを実行できません。
```

**解決方法**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 問題2: パスが見つからない

**エラーメッセージ**:
```
パス 'C:\...\venv\Scripts\Activate.ps1' が見つかりません。
```

**解決方法**:
1. 現在のディレクトリを確認：
   ```powershell
   Get-Location
   ```

2. `backend`ディレクトリに移動：
   ```powershell
   cd backend
   ```

3. 仮想環境が存在するか確認：
   ```powershell
   Test-Path venv\Scripts\Activate.ps1
   ```

4. 存在する場合はアクティベート：
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

### 問題3: 仮想環境が存在しない

**解決方法**: 仮想環境を作成：

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
```

## 推奨される作業フロー

1. **プロジェクトのルートディレクトリに移動**:
   ```powershell
   cd C:\github\toybox
   ```

2. **backendディレクトリに移動**:
   ```powershell
   cd backend
   ```

3. **仮想環境をアクティベート**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **確認**:
   ```powershell
   python --version
   ```

5. **Djangoサーバーを起動**:
   ```powershell
   python manage.py runserver
   ```

## 便利なエイリアス（オプション）

PowerShellプロファイルにエイリアスを追加すると便利です：

```powershell
# PowerShellプロファイルを開く
notepad $PROFILE

# 以下の行を追加
function Activate-Toybox {
    cd C:\github\toybox\backend
    .\venv\Scripts\Activate.ps1
}

# 保存後、PowerShellを再起動
# 使用時: Activate-Toybox
```

## 注意事項

- 仮想環境をアクティベートした後は、プロンプトの前に`(venv)`が表示されます
- 仮想環境を無効化するには、`deactivate`コマンドを実行します
- 新しいPowerShellウィンドウを開いた場合は、再度アクティベートする必要があります
