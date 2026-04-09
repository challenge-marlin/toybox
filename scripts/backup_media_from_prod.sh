#!/bin/bash
# メディアボリューム本番環境バックアップスクリプト
# 本番サーバー上で実行してください

set -e

# 設定
BACKUP_DIR="/backup/toybox/media"
DATE=$(date +%Y%m%d_%H%M%S)
VOLUME_NAME="backend_media_volume"
BACKUP_FILE="${BACKUP_DIR}/media_volume_${DATE}.tar.gz"
INFO_FILE="${BACKUP_DIR}/media_backup_${DATE}_info.txt"

# 色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "メディアボリュームバックアップ開始"
echo "========================================"
echo "日時: ${DATE}"
echo "ボリューム: ${VOLUME_NAME}"
echo ""

# バックアップディレクトリを作成
echo "📁 バックアップディレクトリを作成..."
sudo mkdir -p ${BACKUP_DIR}

# メディアボリュームをバックアップ
echo "💾 メディアボリュームをバックアップ中..."
sudo docker run --rm \
  -v ${VOLUME_NAME}:/source:ro \
  -v ${BACKUP_DIR}:/backup \
  alpine tar czf /backup/media_volume_${DATE}.tar.gz -C /source .

# バックアップファイルの存在確認
if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}❌ バックアップファイルの作成に失敗しました${NC}"
    exit 1
fi

# バックアップファイルのサイズ表示
BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
echo -e "${GREEN}✅ バックアップファイル作成完了: ${BACKUP_SIZE}${NC}"

# ファイル数をカウント
echo "📊 バックアップ情報を記録中..."
FILE_COUNT=$(sudo tar tzf ${BACKUP_FILE} | grep -v '/$' | wc -l)

# バックアップ情報を記録
cat > ${INFO_FILE} <<EOF
バックアップ日時: ${DATE}
元のボリューム: ${VOLUME_NAME}
ファイル数: ${FILE_COUNT}
バックアップサイズ: ${BACKUP_SIZE}
バックアップファイル: media_volume_${DATE}.tar.gz
EOF

echo -e "${GREEN}✅ バックアップ情報を記録しました${NC}"

# ハッシュ値を計算
echo "🔐 ハッシュ値を計算中..."
sha256sum ${BACKUP_FILE} > ${BACKUP_FILE}.sha256
echo -e "${GREEN}✅ ハッシュ値を記録しました${NC}"

# バックアップ内容のサンプル表示
echo ""
echo "📄 バックアップ内容のサンプル（最初の20ファイル）:"
sudo tar tzf ${BACKUP_FILE} | head -20

# 完了メッセージ
echo ""
echo "========================================"
echo -e "${GREEN}✅ バックアップが完了しました${NC}"
echo "========================================"
echo "バックアップファイル: ${BACKUP_FILE}"
echo "情報ファイル: ${INFO_FILE}"
echo "ハッシュファイル: ${BACKUP_FILE}.sha256"
echo ""
echo "次のステップ:"
echo "1. バックアップファイルをローカルにダウンロード"
echo "   scp user@server:${BACKUP_FILE} ./"
echo "   scp user@server:${BACKUP_FILE}.sha256 ./"
echo "   scp user@server:${INFO_FILE} ./"
echo ""
echo "2. ローカルでリストアスクリプトを実行"
echo "   ./restore_media_local.ps1 media_volume_${DATE}.tar.gz"
echo ""
