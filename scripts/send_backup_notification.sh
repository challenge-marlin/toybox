#!/bin/bash
# バックアップ通知メール送信スクリプト
# 使用方法: send_backup_notification.sh <success|failure> <backup_type> <details>

STATUS=$1
BACKUP_TYPE=$2
DETAILS=$3

# メール送信先
TO_EMAILS="maki@ayatori-inc.co.jp,tech@ayatori-inc.co.jp"

# メールサーバー設定（環境に応じて変更）
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER="your-email@gmail.com"
SMTP_PASS="your-app-password"

# メール内容を生成
if [ "$STATUS" = "success" ]; then
    SUBJECT="✅ TOYBOXバックアップ成功 - $BACKUP_TYPE"
    PRIORITY="Normal"
    COLOR="成功"
else
    SUBJECT="❌ TOYBOXバックアップ失敗 - $BACKUP_TYPE"
    PRIORITY="High"
    COLOR="失敗"
fi

DATE=$(date "+%Y年%m月%d日 %H:%M:%S")
HOSTNAME=$(hostname)

# メール本文を作成
cat > /tmp/backup_notification.txt << EOF
From: TOYBOX Backup System <noreply@toybox.ayatori-inc.co.jp>
To: $TO_EMAILS
Subject: $SUBJECT
Content-Type: text/plain; charset=UTF-8

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOYBOX バックアップ通知
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【ステータス】$COLOR
【バックアップ種別】$BACKUP_TYPE
【日時】$DATE
【サーバー】$HOSTNAME

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【詳細】
$DETAILS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

このメールは自動送信されています。
TOYBOX バックアップシステム
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

# msmtpを使ってメール送信
if command -v msmtp &> /dev/null; then
    cat /tmp/backup_notification.txt | msmtp --from=noreply@toybox.ayatori-inc.co.jp -t $TO_EMAILS
    SEND_RESULT=$?
else
    # msmtpがない場合はmailコマンドを試す
    if command -v mail &> /dev/null; then
        mail -s "$SUBJECT" $TO_EMAILS < /tmp/backup_notification.txt
        SEND_RESULT=$?
    else
        echo "メール送信コマンドが見つかりません（msmtpまたはmail）"
        SEND_RESULT=1
    fi
fi

# 一時ファイル削除
rm -f /tmp/backup_notification.txt

exit $SEND_RESULT
