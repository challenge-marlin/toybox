#!/bin/bash
# TOYBOXボリューム差分バックアップスクリプト
# 作成日：2026年1月23日

BACKUP_DIR="/backup/toybox/volumes-incremental"
DATE=$(date +%Y%m%d)
LOGFILE="/var/log/toybox_backup.log"

echo "======================================" >> $LOGFILE
echo "Incremental volume backup started at $(date)" >> $LOGFILE

# バックアップディレクトリが存在しない場合は作成
mkdir -p $BACKUP_DIR

# 最新の完全バックアップを探す
LATEST_BASE=$(find $BACKUP_DIR -maxdepth 1 -type d -name "base_*" | sort -r | head -1)

# 完全バックアップが存在しない、または7日以上古い場合は完全バックアップを作成
if [ -z "$LATEST_BASE" ] || [ $(find "$LATEST_BASE" -mtime +7 | wc -l) -gt 0 ]; then
    echo "Creating new full backup (base)..." >> $LOGFILE
    
    BASE_DIR="$BACKUP_DIR/base_$DATE"
    mkdir -p "$BASE_DIR"
    
    # PostgreSQLボリュームの完全バックアップ
    if docker run --rm \
      -v backend_postgres_data:/source:ro \
      -v "$BASE_DIR":/backup \
      alpine sh -c "cp -a /source /backup/postgres_data" 2>> $LOGFILE; then
        echo "✅ postgres_data full backup successful" >> $LOGFILE
    else
        echo "❌ postgres_data full backup failed!" >> $LOGFILE
        exit 1
    fi
    
    # メディアボリュームの完全バックアップ
    if docker run --rm \
      -v backend_media_volume:/source:ro \
      -v "$BASE_DIR":/backup \
      alpine sh -c "cp -a /source /backup/media_volume" 2>> $LOGFILE; then
        echo "✅ media_volume full backup successful" >> $LOGFILE
    else
        echo "❌ media_volume full backup failed!" >> $LOGFILE
        exit 1
    fi
    
    LATEST_BASE="$BASE_DIR"
    echo "Full backup created: $BASE_DIR" >> $LOGFILE
else
    echo "Using existing base: $LATEST_BASE" >> $LOGFILE
fi

# 差分バックアップを作成
INCR_DIR="$BACKUP_DIR/incr_$DATE"
mkdir -p "$INCR_DIR"

# PostgreSQLボリュームの差分バックアップ（rsync使用）
echo "Creating incremental backup for postgres_data..." >> $LOGFILE
if docker run --rm \
  -v backend_postgres_data:/source:ro \
  -v "$LATEST_BASE/postgres_data":/base:ro \
  -v "$INCR_DIR":/backup \
  alpine sh -c "
    apk add --no-cache rsync > /dev/null 2>&1
    rsync -a --delete --link-dest=/base /source/ /backup/postgres_data/
  " 2>> $LOGFILE; then
    SIZE=$(du -sh "$INCR_DIR/postgres_data" | cut -f1)
    echo "✅ postgres_data incremental backup successful: $SIZE" >> $LOGFILE
else
    echo "❌ postgres_data incremental backup failed!" >> $LOGFILE
fi

# メディアボリュームの差分バックアップ
echo "Creating incremental backup for media_volume..." >> $LOGFILE
if docker run --rm \
  -v backend_media_volume:/source:ro \
  -v "$LATEST_BASE/media_volume":/base:ro \
  -v "$INCR_DIR":/backup \
  alpine sh -c "
    apk add --no-cache rsync > /dev/null 2>&1
    rsync -a --delete --link-dest=/base /source/ /backup/media_volume/
  " 2>> $LOGFILE; then
    SIZE=$(du -sh "$INCR_DIR/media_volume" | cut -f1)
    echo "✅ media_volume incremental backup successful: $SIZE" >> $LOGFILE
else
    echo "❌ media_volume incremental backup failed!" >> $LOGFILE
fi

# 14日以上古いバックアップを削除
OLD_BASES=$(find $BACKUP_DIR -maxdepth 1 -type d -name "base_*" -mtime +14)
OLD_INCRS=$(find $BACKUP_DIR -maxdepth 1 -type d -name "incr_*" -mtime +14)

OLD_COUNT=$(echo "$OLD_BASES $OLD_INCRS" | wc -w)
if [ $OLD_COUNT -gt 0 ]; then
    echo "Removing $OLD_COUNT old backup(s)" >> $LOGFILE
    echo "$OLD_BASES $OLD_INCRS" | xargs rm -rf
fi

# 現在のバックアップ数を表示
BASE_COUNT=$(find $BACKUP_DIR -maxdepth 1 -type d -name "base_*" | wc -l)
INCR_COUNT=$(find $BACKUP_DIR -maxdepth 1 -type d -name "incr_*" | wc -l)
echo "Total base backups: $BASE_COUNT, incremental backups: $INCR_COUNT" >> $LOGFILE
echo "Incremental volume backup completed at $(date)" >> $LOGFILE

exit 0
