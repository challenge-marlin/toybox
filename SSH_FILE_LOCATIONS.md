# SSH関連ファイルの保存場所（Windows）

## Windows側のファイル保存場所

### 1. SSH公開鍵・秘密鍵の保存場所

#### デフォルトの場所
```
C:\Users\[あなたのユーザー名]\.ssh\
```

#### 具体的なファイル
- **秘密鍵**: `C:\Users\[あなたのユーザー名]\.ssh\id_rsa`
- **公開鍵**: `C:\Users\[あなたのユーザー名]\.ssh\id_rsa.pub`
- **known_hosts**: `C:\Users\[あなたのユーザー名]\.ssh\known_hosts`

#### 確認方法（PowerShell）

```powershell
# 現在のユーザーのホームディレクトリを確認
echo $env:USERPROFILE

# SSHディレクトリの存在確認
Test-Path "$env:USERPROFILE\.ssh"

# SSHディレクトリの中身を確認
Get-ChildItem "$env:USERPROFILE\.ssh"

# 公開鍵の内容を表示
type "$env:USERPROFILE\.ssh\id_rsa.pub"
```

#### もし.sshディレクトリが存在しない場合

SSHキーを生成すると自動的に作成されます：

```powershell
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

実行すると、以下のように聞かれます：
```
Enter file in which to save the key (C:\Users\YourName/.ssh/id_rsa):
```

**デフォルトのままEnterを押す**と、`C:\Users\YourName\.ssh\` に保存されます。

### 2. WinSCPの設定ファイルの保存場所

#### 設定ファイルの場所
```
C:\Users\[あなたのユーザー名]\AppData\Roaming\WinSCP.ini
```

または、WinSCPの設定によっては：
```
C:\Users\[あなたのユーザー名]\Documents\WinSCP.ini
```

#### 確認方法

1. **WinSCPから確認**:
   - WinSCPを起動
   - 「設定」→「設定の保存先」を確認

2. **エクスプローラーから確認**:
   - `Win + R` キーを押す
   - `%APPDATA%\WinSCP` と入力してEnter
   - `WinSCP.ini` ファイルを確認

#### WinSCPの設定を保存する方法

1. WinSCPを起動
2. 「新しいサイト」で接続情報を入力
3. 「保存」ボタンをクリック
4. サイト名を入力（例: `toybox-server`）
5. 「OK」をクリック

これで、次回から「サイト」一覧から選択して接続できます。

### 3. known_hostsファイル（サーバーのホストキー）

#### 保存場所
```
C:\Users\[あなたのユーザー名]\.ssh\known_hosts
```

このファイルには、接続したことのあるサーバーのホストキーが保存されます。

#### 確認方法

```powershell
# known_hostsファイルの内容を確認
type "$env:USERPROFILE\.ssh\known_hosts"
```

#### 特定のサーバーを削除する場合

```powershell
# 160.251.168.144のホストキーを削除
ssh-keygen -R 160.251.168.144
```

## サーバー側のファイル保存場所

### appユーザーの場合

- **ホームディレクトリ**: `/home/app`
- **SSH設定ディレクトリ**: `/home/app/.ssh/`
- **公開鍵リスト**: `/home/app/.ssh/authorized_keys`

### rootユーザーの場合

- **ホームディレクトリ**: `/root`
- **SSH設定ディレクトリ**: `/root/.ssh/`
- **公開鍵リスト**: `/root/.ssh/authorized_keys`

## 実際の設定手順

### ステップ1: Windows側でSSHキーを確認

```powershell
# 現在のユーザー名を確認
$env:USERNAME

# SSHキーが存在するか確認
Test-Path "$env:USERPROFILE\.ssh\id_rsa.pub"

# 存在する場合、公開鍵を表示
if (Test-Path "$env:USERPROFILE\.ssh\id_rsa.pub") {
    type "$env:USERPROFILE\.ssh\id_rsa.pub"
} else {
    Write-Host "SSHキーが見つかりません。生成してください。"
}
```

### ステップ2: SSHキーが存在しない場合の生成

```powershell
# SSHキーを生成
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 保存場所を聞かれたら、デフォルト（Enter）でOK
# パスフレーズは空（Enter）でもOK、または設定してもOK
```

### ステップ3: 公開鍵をサーバーにコピー

```powershell
# 公開鍵をサーバーにコピー
type "$env:USERPROFILE\.ssh\id_rsa.pub" | ssh app@160.251.168.144 "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

パスワード `app_password_123` を入力します。

### ステップ4: WinSCPで公開鍵認証を設定

1. WinSCPを起動
2. 「新しいサイト」をクリック
3. 接続情報を入力：
   - ホスト名: `160.251.168.144`
   - ユーザー名: `app`
   - パスワード: `app_password_123`（初回のみ）
4. 「高度」ボタンをクリック
5. 「SSH」→「認証」を選択
6. 「秘密鍵ファイル」に以下を指定：
   ```
   C:\Users\[あなたのユーザー名]\.ssh\id_rsa
   ```
   または、「参照」ボタンでファイルを選択
7. 「OK」をクリック
8. 「保存」をクリックして設定を保存
9. 「ログイン」をクリックして接続

## よくある質問

### Q: .sshディレクトリが見つからない

**A**: SSHキーを生成すると自動的に作成されます。以下のコマンドで生成：

```powershell
ssh-keygen -t rsa -b 4096
```

### Q: ユーザー名がわからない

**A**: PowerShellで以下を実行：

```powershell
$env:USERNAME
```

または、エクスプローラーで `C:\Users\` を開いて、フォルダ名を確認してください。

### Q: WinSCPの設定ファイルが見つからない

**A**: WinSCPを起動して、「設定」→「設定の保存先」で確認できます。

### Q: 複数のSSHキーを使い分けたい

**A**: 別の名前でキーを生成：

```powershell
ssh-keygen -t rsa -b 4096 -f "$env:USERPROFILE\.ssh\toybox_key"
```

WinSCPでは、その秘密鍵ファイル（`toybox_key`）を指定してください。

## まとめ

### Windows側の重要なパス

| ファイル/ディレクトリ | パス |
|---------------------|------|
| SSHキーディレクトリ | `C:\Users\[ユーザー名]\.ssh\` |
| 秘密鍵 | `C:\Users\[ユーザー名]\.ssh\id_rsa` |
| 公開鍵 | `C:\Users\[ユーザー名]\.ssh\id_rsa.pub` |
| known_hosts | `C:\Users\[ユーザー名]\.ssh\known_hosts` |
| WinSCP設定 | `C:\Users\[ユーザー名]\AppData\Roaming\WinSCP.ini` |

### サーバー側の重要なパス

| ファイル/ディレクトリ | パス（appユーザー） |
|---------------------|-------------------|
| ホームディレクトリ | `/home/app` |
| SSH設定ディレクトリ | `/home/app/.ssh/` |
| 公開鍵リスト | `/home/app/.ssh/authorized_keys` |
