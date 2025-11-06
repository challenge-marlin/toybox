# SSH設定修正手順

## 問題
- 権限エラーが発生した
- SSH設定ファイル名にタイポがあった
- 接続が切れた可能性がある

## 解決方法

### ステップ1: サーバーに再接続

Windows PowerShellで：

```powershell
ssh root@160.251.168.144
```

### ステップ2: SSH設定を修正

サーバー側（rootユーザーで）で、以下のコマンドを**正確に**コピー&ペーストして実行：

```bash
# 誤った設定ファイルを削除（存在する場合）
rm -f /etc/ssh/sshd_configfigg

# SSH設定ファイルのバックアップ
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# パスワード認証を有効化
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 公開鍵認証を有効化
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

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

### ステップ3: appユーザーで接続テスト

Windows PowerShellで：

```powershell
ssh app@160.251.168.144
```

パスワードを聞かれたら、`app_password_123` を入力してください。

### ステップ4: 公開鍵を設定

接続できたら、Windows PowerShell（新しいウィンドウ）で：

```powershell
type $env:USERPROFILE\.ssh\id_rsa.pub | ssh app@160.251.168.144 "cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

パスワード `app_password_123` を入力してください。

## 注意事項

- すべてのコマンドは`root`ユーザーで実行してください
- コマンドは正確にコピー&ペーストしてください
- エラーが出た場合は、そのエラーメッセージを教えてください

