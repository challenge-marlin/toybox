#!/bin/bash
# SSH設定を確実に修正するスクリプト
# rootユーザーで実行してください

set -e

echo "=== SSH設定の最終修正 ==="

# 1. 現在の設定を確認
echo "1. 現在の設定を確認中..."
echo ""
grep -E "^PasswordAuthentication|^PubkeyAuthentication|^#PasswordAuthentication|^#PubkeyAuthentication" /etc/ssh/sshd_config || echo "設定が見つかりません"

# 2. バックアップ
echo ""
echo "2. バックアップを作成中..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d_%H%M%S)
echo "[OK] バックアップを作成しました"

# 3. パスワード認証を確実に有効化
echo ""
echo "3. パスワード認証を有効化中..."

# コメントアウトされている行を有効化
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# noになっている行をyesに変更
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 設定が存在しない場合は追加
if ! grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
    echo "" >> /etc/ssh/sshd_config
    echo "# Password authentication" >> /etc/ssh/sshd_config
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
    echo "[OK] PasswordAuthenticationを追加しました"
fi

# 4. 公開鍵認証を確実に有効化
echo ""
echo "4. 公開鍵認証を有効化中..."

# コメントアウトされている行を有効化
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# noになっている行をyesに変更
sed -i 's/^PubkeyAuthentication no/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# 設定が存在しない場合は追加
if ! grep -q "^PubkeyAuthentication yes" /etc/ssh/sshd_config; then
    echo "" >> /etc/ssh/sshd_config
    echo "# Public key authentication" >> /etc/ssh/sshd_config
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
    echo "[OK] PubkeyAuthenticationを追加しました"
fi

# 5. 設定を確認
echo ""
echo "5. 修正後の設定を確認中..."
echo ""
grep -E "^PasswordAuthentication|^PubkeyAuthentication" /etc/ssh/sshd_config

# 6. SSH設定の構文チェック
echo ""
echo "6. SSH設定の構文チェック中..."
if sshd -t 2>&1; then
    echo "[OK] SSH設定の構文は正しいです"
else
    echo "[エラー] SSH設定に問題があります"
    echo "バックアップから復元してください"
    exit 1
fi

# 7. SSHサービスを停止
echo ""
echo "7. SSHサービスを停止中..."
systemctl stop sshd
sleep 2

# 8. SSHサービスを起動
echo ""
echo "8. SSHサービスを起動中..."
systemctl start sshd
sleep 2

# 9. SSHサービスの状態を確認
echo ""
echo "9. SSHサービスの状態を確認中..."
systemctl status sshd --no-pager -l | head -20

# 10. ポート22がリッスンしているか確認
echo ""
echo "10. ポート22がリッスンしているか確認中..."
if netstat -tlnp 2>/dev/null | grep :22 > /dev/null || ss -tlnp 2>/dev/null | grep :22 > /dev/null; then
    echo "[OK] ポート22がリッスンしています"
else
    echo "[警告] ポート22がリッスンしていない可能性があります"
fi

echo ""
echo "=== 完了 ==="
echo ""
echo "次のステップ:"
echo "1. Windows PowerShellから接続:"
echo "   ssh root@160.251.168.144"
echo "   パスワードを入力してください"
echo ""
echo "2. 接続できない場合は、以下を確認:"
echo "   - ファイアウォール設定"
echo "   - SELinuxの状態"
echo "   - SSHサービスのログ: journalctl -u sshd -n 50"

