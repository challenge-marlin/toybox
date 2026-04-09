#!/bin/bash
# TOYBOXボリューム自動バックアップスクリプト（主にメディア）
# 作成日：2026年1月23日
# 更新日：2026年2月（ファイル名に時刻を含め、data/ネストを作らない）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKUP_DIR="/backup/toybox/volumes"
# 同一バックアップセット（DB + メディア）で時刻を揃えるため、外部から指定できるようにする
# 例: BACKUP_DATE=20260202_210001
DATE="${BACKUP_DATE:-$(date +%Y%m%d_%H%M%S)}"
LOGFILE="/var/log/toybox_backup.log"
NOTIFY_SCRIPT="/var/www/toybox/scripts/send_backup_notification.sh"

# メール通知用の詳細情報を格納
DETAILS=""

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGFILE"
}

log "======================================"
log "Volume backup started at $(date)"

# バックアップディレクトリが存在しない場合は作成
mkdir -p "$BACKUP_DIR"

# メディアボリュームをバックアップ
#
# 重要:
# - -C /data . を使うことで、tar内に「data/」階層を作らない（リストア後の階層ズレを防止）
# - DBは .dump で復元する方針のため、postgres_dataボリュームのtarはこのスクリプトでは作らない
log "Backing up media_volume..."
MEDIA_FILE="$BACKUP_DIR/media_volume_${DATE}.tar.gz"
if docker run --rm \
  -v backend_media_volume:/data \
  -v "$BACKUP_DIR":/backup \
  alpine tar czf "/backup/media_volume_${DATE}.tar.gz" -C /data . 2>> "$LOGFILE"; then
  SIZE=$(du -h "$MEDIA_FILE" | cut -f1)
  log "✅ media_volume backup successful: $SIZE (${MEDIA_FILE})"
  DETAILS="バックアップファイル: media_volume_${DATE}.tar.gz\nファイルサイズ: $SIZE"
else
  log "❌ media_volume backup failed!"
  DETAILS="エラー: media_volume のバックアップに失敗しました\n出力: ${LOGFILE} を確認してください"
  [ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "failure" "メディアボリューム" "$DETAILS" || true
  exit 1
fi

# 古いメディアバックアップ削除（必ず最新1世代のみ保持＝前回分は削除）
# shellcheck source=backup_retention.sh
source "$SCRIPT_DIR/backup_retention.sh"
# DB側の保持方針とは切り離し、メディアは容量が大きいため常に1世代のみ残す
BACKUP_KEEP_GENERATIONS=1 REMOVED_MEDIA=$(retain_newest_backups "$BACKUP_DIR" "media_volume_*.tar.gz")
if [ "${REMOVED_MEDIA:-0}" -gt 0 ]; then
  log "Removed ${REMOVED_MEDIA} old media volume backup(s) (keeping latest 1)"
  DETAILS="$DETAILS\n削除した古いバックアップ: ${REMOVED_MEDIA}個（最新1世代のみ保持）"
fi

BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/media_volume_*.tar.gz 2>/dev/null | wc -l | tr -d '\n\r ')
BACKUP_COUNT=${BACKUP_COUNT:-0}
log "Total media volume backups: $BACKUP_COUNT"
log "Volume backup completed at $(date)"

# メール通知（成功）
[ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "success" "メディアボリューム" "$DETAILS" || true

exit 0
