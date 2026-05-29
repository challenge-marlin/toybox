#!/bin/bash
# TOYBOX 夜間バックアップ（21:00想定）
#
# 方針:
# - DB: pg_dump（.dump）でバックアップ（復元は pg_restore）
# - メディア: Dockerボリュームを tar.gz でバックアップ
# - バックアップ中は Web を停止して、書き込みを止める（事故防止）
#
# 生成物:
# - /backup/toybox/database/toybox_YYYYMMDD_HHMMSS.dump
# - /backup/toybox/volumes/media_volume_YYYYMMDD_HHMMSS.tar.gz

set -euo pipefail

# バックアップ世代保持: 1 = 最新セットのみ（前日分は今回のバックアップ成功後に削除）
# 2 にすると「昨日と今日」の 2 世代を残す。cron や /etc/environment で上書き可。
export BACKUP_KEEP_GENERATIONS="${BACKUP_KEEP_GENERATIONS:-1}"

LOGFILE="/var/log/toybox_backup.log"
BACKEND_DIR="${BACKEND_DIR:-/var/www/toybox/backend}"
SCRIPTS_DIR="${SCRIPTS_DIR:-/var/www/toybox/scripts}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGFILE"
}

compose() {
  (cd "$BACKEND_DIR" && sudo docker compose "$@")
}

RESTORE_RAN=0
restore_services() {
  # 二重実行防止（EXIT と SIGTERM の両方で呼ばれる場合）
  [ "$RESTORE_RAN" = "1" ] && return 0
  RESTORE_RAN=1
  set +e
  log "Restoring services..."
  local attempt ec web_id web_running
  for attempt in 1 2 3; do
    compose up -d web worker beat
    ec=$?
    if [ "$ec" -ne 0 ]; then
      log "❌ docker compose up -d failed (exit $ec, attempt $attempt/3)"
      sleep 8
      continue
    fi
    sleep 3
    # 稼働中スタックの web コンテナを compose から特定して状態確認
    # （旧 backend-web-1 のハードコードをやめ、誤った RESTORE FAILED 判定を防ぐ）
    web_id="$(compose ps -q web 2>/dev/null | head -1)"
    web_running="$(docker inspect -f '{{.State.Running}}' "$web_id" 2>/dev/null)"
    if [ -n "$web_id" ] && [ "$web_running" = "true" ]; then
      log "✅ web container running (attempt $attempt)"
      compose ps >>"$LOGFILE" 2>&1 || true
      log "Nightly backup finished (services restored)"
      return 0
    fi
    log "⚠️ compose succeeded but web container not Running (attempt $attempt/3)"
    sleep 8
  done
  compose ps >>"$LOGFILE" 2>&1 || true
  log "❌ CRITICAL: web not up after backup. Manual: cd $BACKEND_DIR && sudo docker compose up -d web worker beat"
  log "Nightly backup finished (RESTORE FAILED — check docker / disk)"
}

trap restore_services EXIT SIGTERM SIGINT

log "======================================"
log "Nightly backup started"

# ルート領域が極端に少ないときは Web を止めない（止めると復旧も失敗しやすい）
avail_kb=$(df -P / 2>/dev/null | awk 'NR==2 {print $4}')
if [ -z "${avail_kb}" ] || [ "${avail_kb}" -lt 1048576 ]; then
  log "❌ Abort: root filesystem has less than 1GiB free (${avail_kb:-?} KiB). Not stopping web. Free disk and retry."
  trap - EXIT SIGTERM SIGINT
  RESTORE_RAN=1
  exit 0
fi

# 同一バックアップセット（DB + メディア）で同じタイムスタンプを使う
export BACKUP_DATE="${BACKUP_DATE:-$(date +%Y%m%d_%H%M%S)}"
log "Backup timestamp: ${BACKUP_DATE}"

# ============================================================================
# 稼働中スタックの DBコンテナ / メディアボリュームを自動検出
# ----------------------------------------------------------------------------
# 旧スタック(backend-*)をハードコードしていたため、本番(toybox-*)へ移行後も
# 古いDB/メディアをバックアップし続ける不具合があった（2026-05 修正）。
# ここで compose から実体を解決し、サブスクリプトへ環境変数で渡す。
# サービス停止前（=web稼働中）に解決することで web のマウント情報を参照できる。
# ============================================================================
detect_stack_targets() {
  set +e
  local db_id web_id
  db_id="$(compose ps -q db 2>/dev/null | head -1)"
  if [ -n "$db_id" ]; then
    DB_CONTAINER_NAME="$(docker inspect -f '{{.Name}}' "$db_id" 2>/dev/null | sed 's#^/##')"
  fi
  web_id="$(compose ps -q web 2>/dev/null | head -1)"
  if [ -n "$web_id" ]; then
    # /app/public/uploads にマウントされた named volume を取得
    MEDIA_VOLUME_NAME="$(docker inspect "$web_id" \
      --format '{{range .Mounts}}{{if eq .Destination "/app/public/uploads"}}{{.Name}}{{end}}{{end}}' 2>/dev/null)"
  fi
  set -e
}
detect_stack_targets

# 既定値（検出に失敗しても本番 toybox-* を対象にする）
export DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-toybox-db-1}"
export MEDIA_VOLUME_NAME="${MEDIA_VOLUME_NAME:-toybox_media_volume}"
log "Backup targets: DB container=${DB_CONTAINER_NAME}, media volume=${MEDIA_VOLUME_NAME}"

# 1) Web/Worker/Beat を停止（書き込み停止）
log "Stopping services (web/worker/beat) for backup..."
compose stop web worker beat

# 2) DBダンプ（.dump）
log "Running DB dump backup..."
sudo bash "$SCRIPTS_DIR/backup_database.sh"

# 3) メディアボリュームバックアップ（tar.gz）
log "Running media volume backup..."
sudo bash "$SCRIPTS_DIR/backup_volumes.sh"

log "Nightly backup completed successfully"

