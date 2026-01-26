#!/bin/bash
# TOYBOXボリューム自動バックアップスクリプト
# 作成日：2026年1月23日

BACKUP_DIR="/backup/toybox/volumes"
DATE=$(date +%Y%m%d)
LOGFILE="/var/log/toybox_backup.log"

echo "======================================" >> $LOGFILE
echo "Volume backup started at $(date)" >> $LOGFILE

# バックアップディレクトリが存在しない場合は作成
mkdir -p $BACKUP_DIR

# PostgreSQLボリュームをバックアップ
echo "Backing up postgres_data volume..." >> $LOGFILE
if docker run --rm \
  -v backend_postgres_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/postgres_data_$DATE.tar.gz /data 2>> $LOGFILE; then
    SIZE=$(du -h $BACKUP_DIR/postgres_data_$DATE.tar.gz | cut -f1)
    echo "✅ postgres_data backup successful: $SIZE" >> $LOGFILE
else
    echo "❌ postgres_data backup failed!" >> $LOGFILE
fi

# メディアボリュームをバックアップ
echo "Backing up media_volume..." >> $LOGFILE
if docker run --rm \
  -v backend_media_volume:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/media_volume_$DATE.tar.gz /data 2>> $LOGFILE; then
    SIZE=$(du -h $BACKUP_DIR/media_volume_$DATE.tar.gz | cut -f1)
    echo "✅ media_volume backup successful: $SIZE" >> $LOGFILE
else
    echo "❌ media_volume backup failed!" >> $LOGFILE
fi

# 14日以上古いバックアップを削除
OLD_COUNT=$(find $BACKUP_DIR -name "*_*.tar.gz" -mtime +14 | wc -l)
if [ $OLD_COUNT -gt 0 ]; then
    echo "Removing $OLD_COUNT old volume backup(s)" >> $LOGFILE
    find $BACKUP_DIR -name "*_*.tar.gz" -mtime +14 -delete
fi

BACKUP_COUNT=$(ls -1 $BACKUP_DIR/*_*.tar.gz 2>/dev/null | wc -l)
echo "Total volume backups: $BACKUP_COUNT" >> $LOGFILE
echo "Volume backup completed at $(date)" >> $LOGFILE

exit 0
