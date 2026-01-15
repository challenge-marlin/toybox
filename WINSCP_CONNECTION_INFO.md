# WinSCP接続情報

## 基本接続情報

### サーバー情報
- **ホスト名**: `160.251.168.144`
- **ポート番号**: `22`（デフォルト）
- **プロトコル**: `SFTP` または `SCP`

### ユーザーアカウント

#### 1. rootユーザー（管理者）
- **ユーザー名**: `root`
- **パスワード**: ConoHaの管理画面で確認してください
- **用途**: サーバー管理、初期設定

#### 2. appユーザー（アプリケーション用）
- **ユーザー名**: `app`
- **パスワード**: `app_password_123`
- **用途**: アプリケーションのデプロイ、ファイル管理

## WinSCPでの接続手順

### ステップ1: WinSCPを起動

1. WinSCPを起動します
2. 「新しいサイト」をクリックします

### ステップ2: 接続情報を入力

#### appユーザーで接続する場合（推奨）

```
ファイルプロトコル: SFTP
ホスト名: 160.251.168.144
ポート番号: 22
ユーザー名: app
パスワード: app_password_123
```

#### rootユーザーで接続する場合

```
ファイルプロトコル: SFTP
ホスト名: 160.251.168.144
ポート番号: 22
ユーザー名: root
パスワード: [ConoHa管理画面で確認]
```

### ステップ3: 接続設定

1. 「保存」ボタンをクリックして接続情報を保存
2. 「ログイン」ボタンをクリックして接続

### ステップ4: 初回接続時の確認

初回接続時、サーバーのホストキー確認ダイアログが表示されます：
- 「はい」をクリックして続行
- 「このホストを信頼するホストのリストに追加する」にチェックを入れることを推奨

## SSH公開鍵認証の設定（オプション）

パスワード認証の代わりに、SSH公開鍵認証を使用することもできます。

### ステップ1: SSHキーの生成（まだない場合）

Windows PowerShellで実行：

```powershell
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

キーファイルの保存場所を聞かれたら、デフォルト（`C:\Users\YourName\.ssh\id_rsa`）でEnterを押します。

### ステップ2: 公開鍵をサーバーにコピー

#### 方法A: PowerShell経由でコピー

```powershell
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh app@160.251.168.144 "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

パスワード `app_password_123` を入力します。

#### 方法B: WinSCP経由でコピー

1. WinSCPで接続後、左側（ローカル）で `C:\Users\YourName\.ssh\id_rsa.pub` を選択
2. 右側（サーバー）で `/home/app/.ssh/` ディレクトリに移動
3. ファイルをドラッグ&ドロップでコピー
4. サーバー側で以下を実行（SSH接続またはWinSCPのターミナル機能を使用）：

```bash
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### ステップ3: WinSCPで公開鍵認証を使用

1. WinSCPの接続設定画面で「高度」をクリック
2. 「SSH」→「認証」を選択
3. 「秘密鍵ファイル」に `C:\Users\YourName\.ssh\id_rsa` を指定
4. 「OK」をクリック
5. 接続を試す（パスワード不要になるはず）

## よくある問題と解決方法

### 問題1: 接続できない（Connection refused）

**原因**: SSHサービスが停止している、またはファイアウォールでブロックされている

**解決方法**:
- ConoHaの管理画面からVNCコンソールでサーバーにアクセス
- SSHサービスが起動しているか確認：`systemctl status sshd`
- 起動していない場合は：`systemctl start sshd`

### 問題2: Permission denied（パスワード認証）

**原因**: SSH設定でパスワード認証が無効になっている

**解決方法**: VNCコンソール経由でサーバーにアクセスし、以下を実行：

```bash
# SSH設定を編集
vi /etc/ssh/sshd_config

# 以下の行を確認/変更：
PasswordAuthentication yes
PubkeyAuthentication yes

# SSHサービスを再起動
systemctl restart sshd
```

### 問題3: 公開鍵認証が機能しない

**原因**: サーバー側の権限設定が正しくない

**解決方法**: サーバー側で以下を実行：

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chown -R app:app ~/.ssh  # appユーザーの場合
```

## 重要なディレクトリ

### appユーザーの場合
- **ホームディレクトリ**: `/home/app`
- **プロジェクトディレクトリ**: `/home/app/toybox`（存在する場合）
- **SSH設定**: `/home/app/.ssh/`

### rootユーザーの場合
- **ホームディレクトリ**: `/root`
- **SSH設定**: `/root/.ssh/`

## セキュリティに関する注意事項

1. **パスワードの管理**: パスワードは安全に管理してください
2. **公開鍵認証の推奨**: セキュリティのため、可能な限り公開鍵認証を使用してください
3. **rootユーザーの使用**: 通常の作業は`app`ユーザーを使用し、`root`は必要な時のみ使用してください
4. **ファイアウォール**: ConoHaの管理画面でSSHポート（22）が適切に設定されているか確認してください

## 接続テスト

接続が成功したら、以下のコマンドで確認できます：

```bash
# 現在のユーザーを確認
whoami

# ホームディレクトリを確認
pwd

# ディスク使用量を確認
df -h
```
