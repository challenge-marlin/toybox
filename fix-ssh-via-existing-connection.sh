#!/bin/bash
# SSH設定修正スクリプト（既存の接続方法で実行）

set -e

echo "=== SSH設定修正 ==="

# 1. 誤った設定ファイルを削除
if [ -f /etc/ssh/sshd_configfigg ]; then
    rm -f /etc/ssh/sshd_configfigg
    echo "[OK] 誤った設定ファイルを削除しました"
fi

# 2. SSH設定ファイルのバックアップ
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)
echo "[OK] SSH設定ファイルをバックアップしました"

# 3. パスワード認証を有効化
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 4. 公開鍵認証を有効化
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 5. 設定が存在しない場合は追加
if ! grep -q "^PasswordAuthentication" /etc/ssh/sshd_config; then
    echo "" >> /etc/ssh/sshd_config
    echo "# Password authentication" >> /etc/ssh/sshd_config
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
    echo "[OK] PasswordAuthenticationを追加しました"
fi

if ! grep -q "^PubkeyAuthentication" /etc/ssh/sshd_config; then
    echo "" >> /etc/ssh/sshd_config
    echo "# Public key authentication" >> /etc/ssh/sshd_config
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
    echo "[OK] PubkeyAuthenticationを追加しました"
fi

# 6. 設定を確認
echo ""
echo "現在の設定:"
grep -E "^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config || echo "設定が見つかりません"

# 7. SSH設定の構文チェック
echo ""
echo "SSH設定の構文チェック中..."
if sshd -t 2>&1; then
    echo "[OK] SSH設定の構文は正しいです"
else
    echo "[エラー] SSH設定に問題があります"
    echo "バックアップから復元してください:"
    echo "cp /etc/ssh/sshd_config.backup.* /etc/ssh/sshd_config"
    exit 1
fi

# 8. SSHサービスを再起動
echo ""
echo "SSHサービスを再起動中..."
systemctl restart sshd
if [ $? -eq 0 ]; then
    echo "[OK] SSHサービスを再起動しました"
else
    echo "[警告] SSHサービスの再起動に失敗しました"
    echo "手動で再起動してください: systemctl restart sshd"
fi

echo ""
echo "=== 完了 ==="
echo ""
echo "次のステップ:"
echo "1. Windows PowerShellから接続:"
echo "   ssh root@160.251.168.144"
echo "   パスワードを入力してください"
echo ""
echo "2. 接続できたら、appユーザーのセットアップを続行してください"

