#!/bin/bash
# TOYBOXデータベース自動バックアップスクリプト
# 作成日：2026年1月23日
# 更新日：2026年1月30日（.dump形式（カスタムフォーマット）に変更、文字化け完全対策）

set -euo pipefail  # エラー時に即座に終了、未定義変数の使用を防ぐ

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# （任意）DBダンプ（.dump）を無効化したい場合
# ----------------------------------------------------------------------------
# 事故対応などで「今日はDBダンプを作りたくない」ケース向け。
# ENABLE_DB_DUMP_BACKUP=false の場合、このスクリプトは何もせず終了します。
# ============================================================================

if [ "${ENABLE_DB_DUMP_BACKUP:-true}" != "true" ]; then
  LOGFILE="/var/log/toybox_backup.log"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⏭️ DB dump backup skipped (ENABLE_DB_DUMP_BACKUP=${ENABLE_DB_DUMP_BACKUP})" >> "$LOGFILE"
  exit 0
fi

# ============================================================================
# 設定
# ============================================================================

BACKUP_DIR="/backup/toybox/database"
# 同一バックアップセット（DB + メディア）で時刻を揃えるため、外部から指定できるようにする
# 例: BACKUP_DATE=20260202_210001
DATE="${BACKUP_DATE:-$(date +%Y%m%d_%H%M%S)}"
LOGFILE="/var/log/toybox_backup.log"
NOTIFY_SCRIPT="/var/www/toybox/scripts/send_backup_notification.sh"
CONTAINER_NAME="backend-db-1"
DATABASE_NAME="toybox"
DB_USER="postgres"

# メール通知用の詳細情報を格納
DETAILS=""

# ============================================================================
# 関数定義
# ============================================================================

# ログ出力関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOGFILE"
}

# エラー処理関数
error_exit() {
    log "❌ ERROR: $1"
    DETAILS="$DETAILS\nエラー: $1"
    [ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "failure" "PostgreSQLダンプ" "$DETAILS" || true
    exit 1
}

# ============================================================================
# 初期化
# ============================================================================

log "======================================"
log "Backup started at $(date)"

# バックアップディレクトリが存在しない場合は作成
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR" || error_exit "バックアップディレクトリの作成に失敗しました: $BACKUP_DIR"
    log "バックアップディレクトリを作成しました: $BACKUP_DIR"
fi

# Dockerコンテナが起動しているか確認
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    error_exit "Dockerコンテナが起動していません: $CONTAINER_NAME"
fi

# PostgreSQLが接続可能か確認
if ! docker exec "$CONTAINER_NAME" pg_isready -U "$DB_USER" > /dev/null 2>&1; then
    error_exit "PostgreSQLに接続できません: $CONTAINER_NAME"
fi

# ============================================================================
# バックアップ実行
# ============================================================================

BACKUP_FILE="${BACKUP_DIR}/toybox_${DATE}.dump"

log "バックアップファイル: $BACKUP_FILE"

# PostgreSQLダンプを実行（カスタムフォーマット）
# オプション説明:
#   -F c (--format=custom)   : カスタムフォーマット（バイナリ、圧縮済み、確実）
#   --encoding=UTF8          : 文字エンコーディングをUTF-8に明示的に指定（文字化けを防ぐ）
#   --no-owner               : オーナー情報を除外（復元時のエラーを避ける）
#   --no-privileges          : 権限情報を除外（復元時のエラーを避ける）
#   --verbose                : 詳細なログ出力
#
# カスタムフォーマット（.dump）の利点:
#   ✅ バイナリ形式で文字化けが起きない
#   ✅ 自動的に圧縮される
#   ✅ pg_restoreで確実にリストアできる
#   ✅ 大規模データに適している
log "PostgreSQLダンプを実行中（カスタムフォーマット）..."

if docker exec -e PGCLIENTENCODING=UTF8 -e LANG=C.UTF-8 "$CONTAINER_NAME" pg_dump \
    -U "$DB_USER" \
    -F c \
    --encoding=UTF8 \
    --no-owner \
    --no-privileges \
    --verbose \
    "$DATABASE_NAME" \
    2>> "$LOGFILE" > "$BACKUP_FILE"; then
    
    log "✅ Backup successful: toybox_${DATE}.dump"
else
    error_exit "pg_dumpの実行に失敗しました"
fi

# ============================================================================
# バックアップファイルの検証
# ============================================================================

# ファイルサイズを確認
if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "バックアップファイルが作成されませんでした: $BACKUP_FILE"
fi

FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
FILE_SIZE_BYTES=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "0")

log "File size: $FILE_SIZE ($FILE_SIZE_BYTES bytes)"
DETAILS="バックアップファイル: toybox_${DATE}.dump\nファイルサイズ: $FILE_SIZE"

# ファイルサイズが0バイトの場合はエラー
if [ "$FILE_SIZE_BYTES" -eq 0 ]; then
    error_exit "バックアップファイルのサイズが0バイトです"
fi

# カスタムフォーマット（.dump）の場合は、pg_restoreで検証
log "バックアップファイルの内容を検証中（カスタムフォーマット）..."

# バックアップファイルをコンテナ内の一時パスにコピーして検証
TEMP_BACKUP_PATH="/tmp/verify_backup_${DATE}.dump"
if docker cp "$BACKUP_FILE" "$CONTAINER_NAME:$TEMP_BACKUP_PATH" 2>> "$LOGFILE"; then
    # pg_restore --list でバックアップファイルの内容を確認
    if ! docker exec "$CONTAINER_NAME" pg_restore --list "$TEMP_BACKUP_PATH" > /dev/null 2>> "$LOGFILE"; then
        docker exec "$CONTAINER_NAME" rm -f "$TEMP_BACKUP_PATH" 2>/dev/null || true
        error_exit "バックアップファイルが破損しています（pg_restore検証失敗）"
    fi
    
    log "✅ Backup file integrity OK (pg_restore check)"
    
    # バックアップに含まれるテーブル数を確認
    TABLE_COUNT=$(docker exec "$CONTAINER_NAME" pg_restore --list "$TEMP_BACKUP_PATH" 2>/dev/null | grep -c "TABLE DATA" 2>/dev/null || echo "0")
    # 改行や空白を削除して数値に変換
    TABLE_COUNT=$(echo "$TABLE_COUNT" | tr -d '\n\r ' || echo "0")
    # 空文字列の場合は0にする
    TABLE_COUNT=${TABLE_COUNT:-0}
    log "Tables found: $TABLE_COUNT"
    DETAILS="$DETAILS\n整合性チェック: OK\nテーブル数: ${TABLE_COUNT}"
    
    # テーブル数が少なすぎる場合は警告
    if [ "$TABLE_COUNT" -lt 5 ]; then
        log "⚠️ Warning: Table count is low ($TABLE_COUNT). Backup might be incomplete."
        DETAILS="$DETAILS\n警告: テーブル数が少ない可能性があります（${TABLE_COUNT}件）"
    fi
    
    # 主要テーブルの存在を確認
    log "主要テーブルの存在を確認中..."
    for TABLE in users cards submissions user_cards announcements titles user_meta; do
        if docker exec "$CONTAINER_NAME" pg_restore --list "$TEMP_BACKUP_PATH" 2>/dev/null | grep -q "TABLE DATA.*${TABLE}"; then
            log "  ✅ ${TABLE}: 見つかりました"
        else
            log "  ⚠️ ${TABLE}: 見つかりませんでした"
        fi
    done
    
    # 一時ファイルを削除
    docker exec "$CONTAINER_NAME" rm -f "$TEMP_BACKUP_PATH" 2>/dev/null || true
else
    log "⚠️ Warning: Could not verify backup file (docker cp failed)"
fi

# ============================================================================
# 古いバックアップの削除（世代数: BACKUP_KEEP_GENERATIONS、既定 1 = 最新のみ）
# ============================================================================

# shellcheck source=backup_retention.sh
source "$SCRIPT_DIR/backup_retention.sh"

REMOVED_DUMP=$(retain_newest_backups "$BACKUP_DIR" "toybox_*.dump")
REMOVED_SQL=$(retain_newest_backups "$BACKUP_DIR" "toybox_*.sql.gz")
REMOVED=$((REMOVED_DUMP + REMOVED_SQL))
if [ "$REMOVED" -gt 0 ]; then
    DETAILS="$DETAILS\n削除した古いバックアップ: ${REMOVED}個（.dump: ${REMOVED_DUMP}, .sql.gz: ${REMOVED_SQL}）"
fi

# 現在のバックアップ数を表示（.dumpと.sql.gz両方）
BACKUP_COUNT_DUMP=$(ls -1 "$BACKUP_DIR"/toybox_*.dump 2>/dev/null | wc -l 2>/dev/null || echo "0")
BACKUP_COUNT_SQLGZ=$(ls -1 "$BACKUP_DIR"/toybox_*.sql.gz 2>/dev/null | wc -l 2>/dev/null || echo "0")
# 改行や空白を削除して数値に変換
BACKUP_COUNT_DUMP=$(echo "$BACKUP_COUNT_DUMP" | tr -d '\n\r ' || echo "0")
BACKUP_COUNT_SQLGZ=$(echo "$BACKUP_COUNT_SQLGZ" | tr -d '\n\r ' || echo "0")
# 空文字列の場合は0にする
BACKUP_COUNT_DUMP=${BACKUP_COUNT_DUMP:-0}
BACKUP_COUNT_SQLGZ=${BACKUP_COUNT_SQLGZ:-0}
BACKUP_COUNT=$((BACKUP_COUNT_DUMP + BACKUP_COUNT_SQLGZ))

log "Total backups: $BACKUP_COUNT (.dump: $BACKUP_COUNT_DUMP, .sql.gz: $BACKUP_COUNT_SQLGZ)"
DETAILS="$DETAILS\n保持しているバックアップ: ${BACKUP_COUNT}個 (.dump: ${BACKUP_COUNT_DUMP}個, .sql.gz: ${BACKUP_COUNT_SQLGZ}個)"

# ============================================================================
# 完了
# ============================================================================

log "Backup completed at $(date)"
log "======================================"

# メール通知（成功）
[ -x "$NOTIFY_SCRIPT" ] && $NOTIFY_SCRIPT "success" "PostgreSQLダンプ" "$DETAILS" || true

exit 0
