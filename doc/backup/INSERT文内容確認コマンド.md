# INSERT文内容確認コマンド

**作成日**: 2026年1月28日  
**目的**: pg_dumpの出力されたINSERT文の内容を確認して、文字化けがないか確認する

---

## 確認コマンド

### ステップ1: INSERT文の内容を直接確認

```bash
# サーバー側で実行
cd /var/www/toybox/backend

# INSERT文のサンプルを確認（日本語が含まれるもの）
echo "=== cardsテーブルのINSERT文（最初の1件） ==="
docker compose exec db pg_dump \
    -U postgres \
    --encoding=UTF8 \
    --no-owner \
    --no-privileges \
    --column-inserts \
    toybox 2>&1 | grep "INSERT INTO.*cards" | head -1

echo ""
echo "=== announcementsテーブルのINSERT文 ==="
docker compose exec db pg_dump \
    -U postgres \
    --encoding=UTF8 \
    --no-owner \
    --no-privileges \
    --column-inserts \
    toybox 2>&1 | grep "INSERT INTO.*announcements" | head -1

echo ""
echo "=== usersテーブルのINSERT文（最初の1件） ==="
docker compose exec db pg_dump \
    -U postgres \
    --encoding=UTF8 \
    --no-owner \
    --no-privileges \
    --column-inserts \
    toybox 2>&1 | grep "INSERT INTO.*users" | head -1
```

### ステップ2: ファイルに保存して内容を確認

```bash
# サーバー側で実行
cd /var/www/toybox/backend

# バックアップファイルを作成（実際のバックアップと同じ方法）
docker compose exec db pg_dump \
    -U postgres \
    --encoding=UTF8 \
    --no-owner \
    --no-privileges \
    --column-inserts \
    toybox 2>&1 | gzip > /tmp/test_backup.sql.gz

# 解凍して内容を確認
gunzip -c /tmp/test_backup.sql.gz > /tmp/test_backup.sql

# INSERT文のサンプルを確認
echo "=== cardsテーブルのINSERT文 ==="
grep "INSERT INTO.*cards" /tmp/test_backup.sql | head -1

echo ""
echo "=== announcementsテーブルのINSERT文 ==="
grep "INSERT INTO.*announcements" /tmp/test_backup.sql | head -1

# 16進数ダンプで確認（文字化けがないか）
echo ""
echo "=== 16進数ダンプ（最初の200バイト） ==="
head -c 200 /tmp/test_backup.sql | od -An -tx1 | head -10
```

### ステップ3: 実際のバックアップファイルを確認

```bash
# サーバー側で実行
# 最新のバックアップファイルを取得
LATEST_BACKUP=$(ls -t /backup/toybox/database/toybox_*.sql.gz | head -1)
echo "確認するファイル: $LATEST_BACKUP"

# 解凍して内容を確認
gunzip -c "$LATEST_BACKUP" > /tmp/latest_backup.sql

# INSERT文のサンプルを確認
echo "=== cardsテーブルのINSERT文 ==="
grep "INSERT INTO.*cards" /tmp/latest_backup.sql | head -1

echo ""
echo "=== announcementsテーブルのINSERT文 ==="
grep "INSERT INTO.*announcements" /tmp/latest_backup.sql | head -1

# ファイルサイズを確認
echo ""
echo "=== ファイル情報 ==="
ls -lh /tmp/latest_backup.sql
wc -l /tmp/latest_backup.sql
```

---

## 期待される結果

### 正常な場合

INSERT文に日本語が正しく含まれている：
```sql
INSERT INTO cards (id, code, name, ...) VALUES (1, 'C001', '見習いプランナー', ...);
```

### 問題がある場合

INSERT文に文字化けが発生している：
```sql
INSERT INTO cards (id, code, name, ...) VALUES (1, 'C001', '????????', ...);
```

---

上記のコマンドを実行して、INSERT文の内容を確認してください。特に、日本語が正しく含まれているかどうかを確認してください。

---

**TOYBOX開発チーム**  
**2026年1月28日**
