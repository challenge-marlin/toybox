# VNCコンソール経由でのアクセス手順

## 問題
SSH接続ができないため、ConoHaの管理画面からVNCコンソールで直接アクセスする必要があります。

## 手順

### ステップ1: ConoHaの管理画面にアクセス

1. ConoHaの管理画面にログイン
2. サーバー一覧から該当サーバーを選択
3. 「VNCコンソール」または「コンソール」をクリック

### ステップ2: VNCコンソールでログイン

VNCコンソールが開いたら、`root`ユーザーでログインしてください。

### ステップ3: SSH設定を修正

VNCコンソール内で、以下のコマンドを実行：

```bash
# SSH設定ファイルのバックアップ
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# パスワード認証を有効化
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 公開鍵認証を有効化
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 設定を確認
grep -E "^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config

# 設定が存在しない場合は追加
if ! grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
fi

if ! grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config; then
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
fi

# SSH設定の構文チェック
sshd -t

# SSHサービスを再起動
systemctl restart sshd

echo "完了！"
```

### ステップ4: Windows PowerShellから接続

Windows PowerShellで：

```powershell
ssh root@160.251.168.144
```

パスワードを聞かれたら、rootユーザーのパスワードを入力してください。

## 代替方法：既存の接続を確認

もし既に別の方法でサーバーにアクセスできている場合は、その方法を使ってSSH設定を修正してください。

