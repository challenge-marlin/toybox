#!/bin/bash
# TOYBOX バックアップ世代管理（最新 N 世代以外を削除）
#
# 環境変数 BACKUP_KEEP_GENERATIONS（デフォルト 1）:
#   1 … 直近のバックアップのみ残す（新規作成後、それより古いファイルを削除＝前日分を消すのと同じ運用）
#   2 … 最新 2 世代を残す
#
# 呼び出し元で log() を定義してから source すること。

retain_newest_backups() {
  local dir="$1"
  local name_glob="$2"
  local keep="${BACKUP_KEEP_GENERATIONS:-1}"

  [ -d "$dir" ] || return 0
  [[ "$keep" =~ ^[0-9]+$ ]] && [ "$keep" -ge 1 ] || keep=1

  mapfile -t kill_list < <(
    find "$dir" -maxdepth 1 -type f -name "$name_glob" -printf '%T@\t%p\n' 2>/dev/null |
      sort -t $'\t' -gr |
      tail -n +$((keep + 1)) |
      cut -f2-
  )

  local f count=0
  for f in "${kill_list[@]}"; do
    [ -z "$f" ] || [ ! -f "$f" ] && continue
    log "🗑️ Removing old backup (keeping latest ${keep}): $f"
    rm -f "$f"
    count=$((count + 1))
  done

  echo "$count"
}
