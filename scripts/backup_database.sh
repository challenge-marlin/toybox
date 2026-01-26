#!/bin/bash
# TOYBOXデータベース自動バックアップスクリプト
# 作成日：2026年1月23日

BACKUP_DIR="/backup/toybox/database"
DATE=$(date +%Y%m%d_%H%M%S)
LOGFILE="/var/log/toybox_backup.log"
NOTIFY_SCRIPT="/var/www/toybox/scripts/send_backup_notification.sh"

# メール通知用の詳細情報を格納
DETAILS=""

echo "======================================" >> $LOGFILE
echo "Backup started at $(date)" >> $LOGFILE

# バックアップディレクトリが存在しない場合は作成
mkdir -p $BACKUP_DIR

# PostgreSQLダンプを実行
if docker exec backend-db-1 pg_dump -U postgres toybox | gzip > $BACKUP_DIR/toybox_$DATE.sql.gz; then
    echo "✅ Backup successful: toybox_$DATE.sql.gz" >> $LOGFILE
    
    # ファイルサイズを確認
    SIZE=$(du -h $BACKUP_DIR/toybox_$DATE.sql.gz | cut -f1)
    echo "File size: $SIZE" >> $LOGFILE
    DETAILS="バックアップファイル: toybox_$DATE.sql.gz\nファイルサイズ: $SIZE"
    
    # バックアップファイルが正常か簡易チェック
    if gunzip -t $BACKUP_DIR/toybox_$DATE.sql.gz 2>> $LOGFILE; then
        echo "✅ Backup file integrity OK" >> $LOGFILE
        DETAILS="$DETAILS\n整合性チェック: OK"
    else
        echo "❌ Backup file is corrupted!" >> $LOGFILE
        DETAILS="$DETAILS\n整合性チェック: 失敗（ファイルが破損しています）"
        # メール通知（失敗）
        [ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "failure" "PostgreSQLダンプ" "$DETAILS"
        exit 1
    fi
    
    # 7日以上古いバックアップを削除
    OLD_COUNT=$(find $BACKUP_DIR -name "toybox_*.sql.gz" -mtime +7 | wc -l)
    if [ $OLD_COUNT -gt 0 ]; then
        echo "Removing $OLD_COUNT old backup(s)" >> $LOGFILE
        find $BACKUP_DIR -name "toybox_*.sql.gz" -mtime +7 -delete
        DETAILS="$DETAILS\n削除した古いバックアップ: ${OLD_COUNT}個"
    fi
    
    # 現在のバックアップ数を表示
    BACKUP_COUNT=$(ls -1 $BACKUP_DIR/toybox_*.sql.gz 2>/dev/null | wc -l)
    echo "Total backups: $BACKUP_COUNT" >> $LOGFILE
    echo "Backup completed at $(date)" >> $LOGFILE
    DETAILS="$DETAILS\n保持しているバックアップ: ${BACKUP_COUNT}個"
    
    # メール通知（成功）
    [ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "success" "PostgreSQLダンプ" "$DETAILS"
    
    exit 0
else
    echo "❌ Backup failed!" >> $LOGFILE
    DETAILS="バックアップ実行に失敗しました。\nDockerコンテナが起動しているか確認してください。"
    # メール通知（失敗）
    [ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "failure" "PostgreSQLダンプ" "$DETAILS"
    exit 1
fi
