#!/bin/bash
# SSH設定修正スクリプト
# rootユーザーで実行してください

set -e

echo "=== SSH設定修正 ==="

# 1. 誤った設定ファイルを削除（存在する場合）
if [ -f /etc/ssh/sshd_configfigg ]; then
    rm -f /etc/ssh/sshd_configfigg
    echo "[OK] 誤った設定ファイルを削除しました"
fi

# 2. SSH設定ファイルのバックアップ
if [ ! -f /etc/ssh/sshd_config.backup ]; then
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    echo "[OK] SSH設定ファイルをバックアップしました"
fi

# 3. パスワード認証を有効化
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 4. 公開鍵認証を有効化
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 5. 設定を確認
echo ""
echo "設定確認:"
grep -E "^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config || echo "設定が見つかりません（追加が必要）"

# 6. 設定が存在しない場合は追加
if ! grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
    echo "[OK] PasswordAuthenticationを追加しました"
fi

if ! grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config; then
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
    echo "[OK] PubkeyAuthenticationを追加しました"
fi

# 7. SSH設定の構文チェック
if sshd -t; then
    echo "[OK] SSH設定の構文は正しいです"
else
    echo "[エラー] SSH設定に問題があります"
    exit 1
fi

# 8. SSHサービスを再起動
echo ""
echo "SSHサービスを再起動中..."
systemctl restart sshd
echo "[OK] SSHサービスを再起動しました"

echo ""
echo "=== 完了 ==="

