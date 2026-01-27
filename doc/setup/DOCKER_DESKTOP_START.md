# Docker Desktopの起動方法

Docker Desktopが起動していないため、以下の手順で起動してください。

## 起動方法

### 方法1: スタートメニューから起動

1. Windowsのスタートメニューを開く
2. 「Docker Desktop」を検索
3. 「Docker Desktop」アプリをクリックして起動

### 方法2: タスクバーから起動

1. タスクバーの検索ボックスに「Docker Desktop」と入力
2. アプリを選択して起動

### 方法3: コマンドラインから起動

PowerShellで実行：

```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

または、ショートカットの場所が異なる場合：

```powershell
& "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
```

## 起動確認

Docker Desktopが起動したら、以下のコマンドで確認：

```powershell
docker version
```

正常に起動している場合、以下のような出力が表示されます：

```
Client:
 Version:           28.5.1
 API version:       1.51
 ...

Server:
 Engine:
  Version:          ...
  ...
```

## 起動に時間がかかる場合

Docker Desktopの初回起動や再起動時は、以下の処理に時間がかかることがあります：

1. Dockerエンジンの初期化
2. WSL2バックエンドの起動（使用している場合）
3. 仮想マシンの起動

通常、1-2分程度かかります。Docker Desktopのアイコンがタスクバーに表示され、緑色になれば起動完了です。

## トラブルシューティング

### Docker Desktopが起動しない場合

1. **管理者権限で実行**
   - Docker Desktopを右クリック → 「管理者として実行」

2. **Windowsの再起動**
   - システムを再起動してから再度試す

3. **Docker Desktopの再インストール**
   - 最後の手段として、Docker Desktopを再インストール

### WSL2エラーが表示される場合

WSL2を使用している場合、以下のコマンドでWSL2を更新：

```powershell
wsl --update
wsl --set-default-version 2
```

## 起動後の確認

Docker Desktopが起動したら、以下のコマンドでコンテナの状態を確認：

```powershell
# 全てのコンテナを確認
docker ps -a

# 実行中のコンテナのみ確認
docker ps
```

