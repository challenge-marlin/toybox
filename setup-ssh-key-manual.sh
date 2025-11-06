#!/bin/bash
# SSH公開鍵を手動で追加するスクリプト
# rootユーザーで実行してください

set -e

echo "=== SSH公開鍵の手動追加 ==="
echo ""

# 1. rootユーザーの公開鍵を表示
echo "1. rootユーザーの公開鍵を表示:"
echo ""
cat /root/.ssh/id_rsa.pub
echo ""
echo ""

# 2. 公開鍵をappユーザーに追加
echo "2. rootユーザーの公開鍵をappユーザーに追加中..."
cat /root/.ssh/id_rsa.pub >> /home/app/.ssh/authorized_keys
chown app:app /home/app/.ssh/authorized_keys
chmod 600 /home/app/.ssh/authorized_keys
echo "   [OK] 公開鍵を追加しました"

# 3. 権限を確認
echo ""
echo "3. 権限を確認中..."
ls -la /home/app/.ssh/
echo ""

# 4. 接続テスト
echo "4. 接続テスト（rootユーザーから）:"
su - app -c "whoami"
echo "   [OK] appユーザーに切り替え可能"

echo ""
echo "=== 完了 ==="
echo ""
echo "次に、Windows PowerShellから以下を実行:"
echo "ssh app@160.251.168.144"
echo ""
echo "または、rootユーザーの秘密鍵を指定:"
echo "ssh -i ~/.ssh/id_rsa app@160.251.168.144"

