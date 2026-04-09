# TOYBOXデータベース（SQL）バックアップ・リストア完全ガイド

**作成日**: 2026年1月29日  
**対象**: PostgreSQLダンプ（.sql.gz）のバックアップとリストア  
**範囲**: データベースのみ（画像ファイルは含まない）

---

## 📋 目次

1. [概要](#概要)
2. [文字化け問題とは](#文字化け問題とは)
3. [バックアップ方法](#バックアップ方法)
4. [リストア方法](#リストア方法)
5. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### このガイドで扱う内容

✅ PostgreSQLダンプファイル（`.sql.gz`）のバックアップ  
✅ サーバー→サーバーへのリストア（本番環境）  
✅ サーバー→ローカルへのリストア（開発環境）  
✅ 文字化け問題の完全解決

### 扱わない内容

❌ メディアボリューム（画像ファイル）の復元  
❌ Dockerボリュームの完全バックアップ  
❌ 差分バックアップ

---

## 文字化け問題とは

### 症状

データベースから日本語を取得すると、以下のように表示される：

```sql
-- 正常
SELECT name FROM cards WHERE id = 14;
-- 結果: トラブルリキッド・セイバー

-- 文字化け
SELECT name FROM cards WHERE id = 14;
-- 結果: ?????????????
```

### 根本原因

**データベースに保存されている時点で既に文字化けしている**

```bash
# バイト列を確認
docker exec backend-db-1 psql -U postgres -d toybox -c \
  "SELECT encode(name::bytea, 'hex') FROM cards WHERE id = 14;"

# 結果が 3f3f3f3f... (すべて 0x3f = ?) なら、DBに保存時に文字化け
```

### 解決の3ステップ

| ステップ | 内容 | 重要度 |
|---------|------|--------|
| **1. SQLファイルがUTF-8** | バックアップ元のSQLファイルが正しくUTF-8エンコーディング | ⭐⭐⭐ |
| **2. バックアップ取得時にUTF-8設定** | pg_dumpでUTF-8を明示的に指定 | ⭐⭐⭐ |
| **3. リストア時にコンテナ内実行** | PowerShellパイプを使わず、コンテナ内で直接psql実行 | ⭐⭐⭐ |

---

## バックアップ方法

### 【サーバー側】自動バックアップの設定

#### 1. バックアップスクリプトの確認

```bash
# サーバーに接続
ssh -i "C:\Users\ayato\.ssh\toybox-2025-11-06-11-40.pem" root@160.251.168.144

# スクリプトの内容を確認
cat /var/www/toybox/scripts/backup_database.sh
```

#### 2. 必須の設定内容

スクリプトに以下が含まれていることを確認：

```bash
# ✅ 必須オプション
docker exec \
  -e PGCLIENTENCODING=UTF8 \      # ← これがないと文字化け
  -e LANG=C.UTF-8 \                # ← これがないと文字化け
  backend-db-1 pg_dump \
  -U postgres \
  --encoding=UTF8 \                # ← これがないと文字化け
  --column-inserts \               # ← これがないと列順序エラー
  --no-owner \
  --no-privileges \
  toybox | gzip > /backup/toybox/database/toybox_$(date +%Y%m%d_%H%M%S).sql.gz
```

**重要**: この4つの設定がすべて必要です：
1. `-e PGCLIENTENCODING=UTF8`
2. `-e LANG=C.UTF-8`
3. `--encoding=UTF8`
4. `--column-inserts`

#### 3. 自動実行の確認

```bash
# cronの設定を確認
crontab -l | grep backup_database

# 期待される結果: 毎日午前3時に実行
# 0 3 * * * /var/www/toybox/scripts/backup_database.sh
```

### 【ローカル】手動バックアップ

```powershell
# backendディレクトリに移動
cd C:\github\toybox\backend

# バックアップを作成
docker compose exec -T db pg_dump -U postgres toybox > backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql

Write-Host "バックアップ完了" -ForegroundColor Green
```

---

## リストア方法

### ケース1: サーバー→サーバー（本番環境での復元）

#### ステップ1: 現在の状態をバックアップ（必須）

```bash
# サーバーに接続
ssh -i "C:\Users\ayato\.ssh\toybox-2025-11-06-11-40.pem" root@160.251.168.144

# 現在の状態をバックアップ
DATE=$(date +%Y%m%d_%H%M%S)
docker exec backend-db-1 pg_dump -U postgres toybox | gzip > /backup/toybox/database/before_restore_${DATE}.sql.gz

echo "✅ バックアップ完了: before_restore_${DATE}.sql.gz"
```

#### ステップ2: 復元するファイルを選択

```bash
# バックアップファイル一覧を表示（日付順）
ls -lht /backup/toybox/database/toybox_*.sql.gz | head -5

# 復元するファイルを指定
RESTORE_FILE="/backup/toybox/database/toybox_20260129_133225.sql.gz"

echo "復元するファイル: $RESTORE_FILE"
```

#### ステップ3: データベースをリセット

```bash
# データベースを削除・再作成（UTF-8を明示的に指定）
docker exec backend-db-1 psql -U postgres -c "DROP DATABASE IF EXISTS toybox;"
docker exec backend-db-1 psql -U postgres -c "CREATE DATABASE toybox WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"

echo "✅ データベースをリセットしました"
```

#### ステップ4: 復元実行

```bash
# 解凍しながら復元（UTF-8設定を明示）
gunzip -c "$RESTORE_FILE" | docker exec \
  -e PGCLIENTENCODING=UTF8 \
  -e LANG=C.UTF-8 \
  -i backend-db-1 psql -U postgres toybox

echo "✅ 復元完了"
```

#### ステップ5: 確認

```bash
# データ件数を確認
docker exec backend-db-1 psql -U postgres -d toybox -c "SELECT COUNT(*) FROM users;"
docker exec backend-db-1 psql -U postgres -d toybox -c "SELECT COUNT(*) FROM cards;"

# 日本語が正しく表示されるか確認
docker exec backend-db-1 psql -U postgres -d toybox -c "SELECT id, name FROM cards WHERE id = 14;"

# 期待される結果: トラブルリキッド・セイバー（?ではない）
```

---

### ケース2: サーバー→ローカル（開発環境での検証）

#### ステップ1: サーバーからバックアップをダウンロード

**方法A: WinSCP（簡単・推奨）**

1. WinSCPを起動
2. サーバーに接続（160.251.168.144、root）
3. 以下をダウンロード：
   ```
   サーバー側: /backup/toybox/database/toybox_YYYYMMDD_HHMMSS.sql.gz
   ↓
   ローカル: C:\backup\toybox\database\
   ```

**方法B: SCPコマンド**

```powershell
# ダウンロード先を作成
New-Item -ItemType Directory -Path "C:\backup\toybox\database" -Force

# ダウンロード（ファイル名は最新のものに置き換え）
scp -i "C:\Users\ayato\.ssh\toybox-2025-11-06-11-40.pem" `
  root@160.251.168.144:/backup/toybox/database/toybox_20260129_133225.sql.gz `
  C:\backup\toybox\database\

# 確認
Get-ChildItem C:\backup\toybox\database\
```

#### ステップ2: ファイルを解凍

```powershell
# 7-Zipで解凍
$gzFile = "C:\backup\toybox\database\toybox_20260129_133225.sql.gz"
$sqlFile = $gzFile -replace "\.gz$", ""

& "C:\Program Files\7-Zip\7z.exe" e $gzFile "-o$(Split-Path $sqlFile)" -y

# 確認
Write-Host "解凍完了: $sqlFile" -ForegroundColor Green
```

#### ステップ3: SQLファイルがUTF-8か確認

```powershell
# UTF-8として日本語が正しく読めるか確認
Get-Content $sqlFile -Encoding UTF8 | Select-String "トラブル" | Select-Object -First 1

# 期待される結果: INSERT文に「トラブルリキッド・セイバー」が表示される
# もし文字化けしていたら、バックアップ元の取得方法を確認
```

#### ステップ4: ローカル環境のデータベースをリセット

```powershell
# backendディレクトリに移動
cd C:\github\toybox\backend

# 念のため現在の状態をバックアップ
$backupName = "backup_before_restore_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
docker compose exec -T db pg_dump -U postgres toybox > $backupName
Write-Host "現在の状態をバックアップ: $backupName" -ForegroundColor Green

# データベースを削除・再作成
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS toybox;"
docker compose exec db psql -U postgres -c "CREATE DATABASE toybox WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"

Write-Host "データベースをリセットしました" -ForegroundColor Green
```

#### ステップ5: 復元実行（重要：コンテナ内で実行）

**❌ 間違った方法（文字化けする）**

```powershell
# これは文字化けする！
Get-Content $sqlFile -Encoding UTF8 | docker compose exec -T db psql -U postgres toybox
```

**✅ 正しい方法（文字化けしない）**

```powershell
# 方法1: ファイルをコンテナ内にコピーしてから実行（推奨）
docker cp $sqlFile backend-db-1:/tmp/restore.sql

docker exec backend-db-1 bash -c "PGCLIENTENCODING=UTF8 psql -U postgres -d toybox -f /tmp/restore.sql"

Write-Host "復元完了" -ForegroundColor Green

# 一時ファイルを削除
docker exec backend-db-1 rm /tmp/restore.sql
```

```powershell
# 方法2: docker-composeのディレクトリから実行
cd C:\github\toybox\backend

docker cp $sqlFile backend-db-1:/tmp/restore.sql

docker compose exec db bash -c "PGCLIENTENCODING=UTF8 psql -U postgres -d toybox -f /tmp/restore.sql"

Write-Host "復元完了" -ForegroundColor Green
```

#### ステップ6: 確認（文字化けチェック）

```powershell
# データ件数を確認
docker compose exec db psql -U postgres -d toybox -c "SELECT COUNT(*) FROM users;"
docker compose exec db psql -U postgres -d toybox -c "SELECT COUNT(*) FROM cards;"

# 🔍 重要：日本語が正しく表示されるか確認
docker compose exec db psql -U postgres -d toybox -c "SELECT id, code, name, attribute FROM cards WHERE id IN (14, 18);"
```

**期待される結果**：

```
 id | code |            name            | attribute
----+------+----------------------------+-----------
 14 | C015 | トラブルリキッド・セイバー | 水
 18 | C019 | 黄金比を操る構造設計士     | 金
```

**✅ 成功**: 日本語が正しく表示される  
**❌ 失敗**: `?????????????` と表示される → [トラブルシューティング](#トラブルシューティング)へ

---

## トラブルシューティング

### 問題1: 日本語が「?」と表示される

#### 診断手順

```powershell
# ステップ1: データベース内のバイト列を確認
docker exec backend-db-1 psql -U postgres -d toybox -c `
  "SELECT id, encode(name::bytea, 'hex') as name_hex FROM cards WHERE id = 14;"
```

**結果の判定**：

| 結果 | 意味 | 対処 |
|------|------|------|
| `3f3f3f3f3f...` | DBに保存時に文字化け | → **対処A** |
| UTF-8の16進数 | DB内は正常、表示の問題 | → **対処B** |

#### 対処A: データベースに保存時に文字化け（最も多いケース）

**原因**: リストア時にUTF-8設定が不足

**解決方法**:

```powershell
# 1. データをクリア
docker compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS toybox;"
docker compose exec db psql -U postgres -c "CREATE DATABASE toybox WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"

# 2. 正しい方法で再リストア（コンテナ内実行）
docker cp $sqlFile backend-db-1:/tmp/restore.sql
docker exec backend-db-1 bash -c "PGCLIENTENCODING=UTF8 psql -U postgres -d toybox -f /tmp/restore.sql"

# 3. 再確認
docker exec backend-db-1 psql -U postgres -d toybox -c "SELECT id, name FROM cards WHERE id = 14;"
```

#### 対処B: SQLファイル自体が文字化け

**診断**:

```powershell
# SQLファイルをUTF-8として読んで日本語が正しく表示されるか確認
Get-Content $sqlFile -Encoding UTF8 | Select-String "トラブル"
```

**結果が文字化け**の場合：
- バックアップ元のサーバー側スクリプトを修正
- 新しいバックアップを取得してから再度リストア

---

### 問題2: 「no configuration file provided」エラー

**症状**:

```
no configuration file provided: not found
```

**原因**: `docker-compose.yml` がないディレクトリで実行している

**解決方法**:

```powershell
# 方法A: backendディレクトリに移動
cd C:\github\toybox\backend
docker compose exec db psql -U postgres -d toybox -c "SELECT 1;"

# 方法B: dockerコマンドを直接使用（移動不要）
docker exec backend-db-1 psql -U postgres -d toybox -c "SELECT 1;"
```

---

### 問題3: 「database "toybox" does not exist」エラー

**原因**: データベースが存在しない

**解決方法**:

```powershell
# データベースを作成（UTF-8を明示）
docker compose exec db psql -U postgres -c "CREATE DATABASE toybox WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"
```

---

### 問題4: リストア後にWebアプリケーションが起動しない

**原因**: マイグレーションが必要

**解決方法**:

```powershell
cd C:\github\toybox\backend
docker compose exec web python3 manage.py migrate
```

---

## チェックリスト

### バックアップ取得時

- [ ] `PGCLIENTENCODING=UTF8` が設定されている
- [ ] `LANG=C.UTF-8` が設定されている
- [ ] `--encoding=UTF8` オプションがある
- [ ] `--column-inserts` オプションがある
- [ ] バックアップファイルが作成された
- [ ] ファイルサイズが0より大きい

### リストア実行時（サーバー→サーバー）

- [ ] 現在の状態をバックアップした
- [ ] 復元するファイルを確認した
- [ ] データベースをUTF-8指定でリセットした
- [ ] `PGCLIENTENCODING=UTF8` を設定して復元した
- [ ] 日本語が正しく表示された

### リストア実行時（サーバー→ローカル）

- [ ] バックアップファイルをダウンロードした
- [ ] ファイルを解凍した
- [ ] SQLファイルがUTF-8であることを確認した
- [ ] ローカルDBをバックアップした（念のため）
- [ ] データベースをUTF-8指定でリセットした
- [ ] **ファイルをコンテナ内にコピーした**
- [ ] **コンテナ内から直接psqlを実行した**
- [ ] 日本語が正しく表示された（文字化けなし）

---

## まとめ

### 文字化けを防ぐための3つの鉄則

| 鉄則 | 内容 |
|------|------|
| **1. バックアップ取得時** | `PGCLIENTENCODING=UTF8`、`--encoding=UTF8`、`--column-inserts` を設定 |
| **2. リストア時の方法** | PowerShellパイプは使わず、**コンテナ内で直接psql実行** |
| **3. データベース作成** | `CREATE DATABASE` で `ENCODING='UTF8'` を明示的に指定 |

### コマンド早見表

#### バックアップ（サーバー）

```bash
docker exec -e PGCLIENTENCODING=UTF8 -e LANG=C.UTF-8 backend-db-1 pg_dump \
  -U postgres --encoding=UTF8 --column-inserts toybox | gzip > backup.sql.gz
```

#### リストア（サーバー）

```bash
gunzip -c backup.sql.gz | docker exec -e PGCLIENTENCODING=UTF8 -e LANG=C.UTF-8 \
  -i backend-db-1 psql -U postgres toybox
```

#### リストア（ローカル）

```powershell
# ✅ 正しい方法
docker cp backup.sql backend-db-1:/tmp/restore.sql
docker exec backend-db-1 bash -c "PGCLIENTENCODING=UTF8 psql -U postgres -d toybox -f /tmp/restore.sql"

# ❌ 間違った方法（文字化けする）
Get-Content backup.sql | docker exec -T db psql -U postgres toybox
```

---

**TOYBOX開発チーム**  
**2026年1月29日**
