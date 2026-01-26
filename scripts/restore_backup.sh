#!/bin/bash
# TOYBOXバックアップからの復元スクリプト
# 作成日：2026年1月23日

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TOYBOX バックアップ復元ツール"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 復元モードを選択
echo "復元モードを選択してください："
echo "1) PostgreSQLダンプから復元（推奨・高速）"
echo "2) Dockerボリューム完全バックアップから復元"
echo "3) Dockerボリューム差分バックアップから復元"
echo "4) キャンセル"
echo ""
read -p "選択 [1-4]: " mode

case $mode in
    1)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "PostgreSQLダンプから復元"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # バックアップファイル一覧を表示
        echo ""
        echo "利用可能なバックアップファイル："
        ls -lht /backup/toybox/database/toybox_*.sql.gz 2>/dev/null | head -10
        
        # 最新のファイルを取得
        LATEST=$(ls -t /backup/toybox/database/toybox_*.sql.gz 2>/dev/null | head -1)
        
        if [ -z "$LATEST" ]; then
            echo "❌ バックアップファイルが見つかりません"
            exit 1
        fi
        
        echo ""
        echo "最新のバックアップ: $(basename $LATEST)"
        echo ""
        read -p "このファイルから復元しますか？ [y/N]: " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo ""
            echo "⚠️  警告：現在のデータベース内容は上書きされます"
            read -p "本当に実行しますか？ [y/N]: " confirm2
            
            if [ "$confirm2" = "y" ] || [ "$confirm2" = "Y" ]; then
                echo ""
                echo "復元を開始します..."
                
                if gunzip -c $LATEST | docker exec -i backend-db-1 psql -U postgres toybox; then
                    echo ""
                    echo "✅ 復元が完了しました"
                    echo ""
                    echo "データを確認しています..."
                    docker exec backend-web-1 python manage.py shell -c "
from users.models import User
from submissions.models import Submission
from gamification.models import Card, Title
print(f'ユーザー数: {User.objects.count()}')
print(f'投稿数: {Submission.objects.count()}')
print(f'カード数: {Card.objects.count()}')
print(f'称号数: {Title.objects.count()}')
"
                else
                    echo ""
                    echo "❌ 復元に失敗しました"
                    exit 1
                fi
            else
                echo "キャンセルしました"
                exit 0
            fi
        else
            echo "キャンセルしました"
            exit 0
        fi
        ;;
        
    2)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Dockerボリュームから復元"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # バックアップファイル一覧を表示
        echo ""
        echo "利用可能なバックアップファイル："
        ls -lht /backup/toybox/volumes/postgres_data_*.tar.gz 2>/dev/null
        
        # 最新のファイルを取得
        LATEST=$(ls -t /backup/toybox/volumes/postgres_data_*.tar.gz 2>/dev/null | head -1)
        
        if [ -z "$LATEST" ]; then
            echo "❌ バックアップファイルが見つかりません"
            exit 1
        fi
        
        echo ""
        echo "最新のバックアップ: $(basename $LATEST)"
        echo ""
        read -p "このファイルから復元しますか？ [y/N]: " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo ""
            echo "⚠️  警告：データベースコンテナを停止し、ボリュームを削除します"
            read -p "本当に実行しますか？ [y/N]: " confirm2
            
            if [ "$confirm2" = "y" ] || [ "$confirm2" = "Y" ]; then
                echo ""
                echo "コンテナを停止しています..."
                cd /var/www/toybox/backend && docker compose stop db
                
                echo "ボリュームを削除しています..."
                docker volume rm backend_postgres_data
                
                echo "ボリュームを復元しています..."
                docker run --rm \
                  -v backend_postgres_data:/data \
                  -v /backup/toybox/volumes:/backup \
                  alpine sh -c "cd / && tar xzf /backup/$(basename $LATEST)"
                
                echo "コンテナを起動しています..."
                cd /var/www/toybox/backend && docker compose up -d
                
                echo ""
                echo "✅ 復元が完了しました"
                echo "データベースが起動するまで約30秒お待ちください..."
                sleep 30
                
                echo ""
                echo "データを確認しています..."
                docker exec backend-web-1 python manage.py shell -c "
from users.models import User
from submissions.models import Submission
print(f'ユーザー数: {User.objects.count()}')
print(f'投稿数: {Submission.objects.count()}')
"
            else
                echo "キャンセルしました"
                exit 0
            fi
        else
            echo "キャンセルしました"
            exit 0
        fi
        ;;
        
    3)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Dockerボリューム差分バックアップから復元"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # 利用可能な差分バックアップを表示
        echo ""
        echo "利用可能な復元ポイント："
        find /backup/toybox/volumes-incremental -maxdepth 1 -type d -name "incr_*" | sort -r | head -10 | while read dir; do
            echo "  - $(basename $dir)"
        done
        
        echo ""
        read -p "復元する日付を入力 (例: 20260123): " TARGET_DATE
        
        if [ -z "$TARGET_DATE" ]; then
            echo "キャンセルしました"
            exit 0
        fi
        
        INCR_DIR="/backup/toybox/volumes-incremental/incr_$TARGET_DATE"
        if [ ! -d "$INCR_DIR" ]; then
            echo "❌ 指定された日付のバックアップが見つかりません"
            exit 1
        fi
        
        echo ""
        echo "⚠️  警告：データベースコンテナを停止し、ボリュームを削除します"
        read -p "本当に実行しますか？ [y/N]: " confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo ""
            echo "コンテナを停止しています..."
            cd /var/www/toybox/backend && docker compose stop db
            
            echo "ボリュームを削除しています..."
            docker volume rm backend_postgres_data backend_media_volume
            
            # ベースとなる完全バックアップを見つける
            BASE_DIR=$(find /backup/toybox/volumes-incremental -maxdepth 1 -type d -name "base_*" -not -newer "$INCR_DIR" | sort -r | head -1)
            
            echo "ベースから復元しています: $(basename $BASE_DIR)"
            docker run --rm \
              -v backend_postgres_data:/data \
              -v "$BASE_DIR/postgres_data":/source:ro \
              alpine sh -c "cp -a /source/. /data/"
            
            docker run --rm \
              -v backend_media_volume:/data \
              -v "$BASE_DIR/media_volume":/source:ro \
              alpine sh -c "cp -a /source/. /data/"
            
            # 差分を順番に適用
            for DIR in $(find /backup/toybox/volumes-incremental -maxdepth 1 -type d -name "incr_*" -newer "$BASE_DIR" -not -newer "$INCR_DIR" | sort); do
                echo "差分を適用しています: $(basename $DIR)"
                docker run --rm \
                  -v backend_postgres_data:/data \
                  -v "$DIR/postgres_data":/source:ro \
                  alpine sh -c "cp -a /source/. /data/"
                
                docker run --rm \
                  -v backend_media_volume:/data \
                  -v "$DIR/media_volume":/source:ro \
                  alpine sh -c "cp -a /source/. /data/"
            done
            
            echo "コンテナを起動しています..."
            cd /var/www/toybox/backend && docker compose up -d
            
            echo ""
            echo "✅ 復元が完了しました"
            echo "データベースが起動するまで約30秒お待ちください..."
            sleep 30
            
            echo ""
            echo "データを確認しています..."
            docker exec backend-web-1 python manage.py shell -c "
from users.models import User
from submissions.models import Submission
print(f'ユーザー数: {User.objects.count()}')
print(f'投稿数: {Submission.objects.count()}')
"
        else
            echo "キャンセルしました"
            exit 0
        fi
        ;;
        
    4)
        echo "キャンセルしました"
        exit 0
        ;;
        
    *)
        echo "無効な選択です"
        exit 1
        ;;
esac
