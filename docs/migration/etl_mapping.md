# MongoDB → PostgreSQL ETL マッピング表

## 概要

このドキュメントは、MongoDBからPostgreSQLへのデータ移行時のフィールドマッピングを定義します。

## コレクション別マッピング

### users → User

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `_id` | `old_id` | CharField | MongoDBのIDを文字列として保持 |
| `email` | `email` | EmailField | メールアドレス |
| `username` | `username` | CharField | ユーザー名 |
| `displayId` / `anonId` | `display_id` | CharField | 表示ID |
| `role` | `role` | CharField | USER/OFFICE/AYATORI/ADMIN |
| `avatarUrl` | `avatar_url` | URLField | アバター画像URL |
| `isSuspended` / `suspended` | `is_suspended` | BooleanField | 停止フラグ |
| `bannedAt` | `banned_at` | DateTimeField | BAN日時 |
| `warningCount` | `warning_count` | IntegerField | 警告数 |
| `warnings[]` | `warning_notes` | TextField | 警告メッセージを改行区切りで結合 |
| `password` | - | - | `set_password()`で設定 |

**注意事項:**
- `old_id`フィールドにMongoDBの`_id`を保存（ETL追跡用）
- 停止/BAN/警告の概念があれば対応付け
- パスワードはハッシュ化して保存

### userMeta → UserMeta

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `_id` | `old_id` | CharField | MongoDBのIDを文字列として保持 |
| `anonId` | `user` (FK) | ForeignKey | Userを`display_id`で検索 |
| `activeTitle` | `active_title` | CharField | アクティブな称号 |
| `titleColor` | `title_color` | CharField | 称号の色 |
| `activeTitleUntil` | `expires_at` | DateTimeField | 有効期限 |
| - | `expires_at` | DateTimeField | `activeTitleUntil`未設定時は`created_at + 7日` |
| `bio` | `bio` | TextField | 自己紹介 |
| `headerUrl` | `header_url` | URLField | ヘッダー画像URL |
| `lotteryBonusCount` | `lottery_bonus_count` | IntegerField | 抽選ボーナスカウント |

**注意事項:**
- `expires_at`が未設定の場合、`created_at + 7日`をデフォルト値として設定
- `user`は`anonId`または`_id`でUserを検索

### submissions → Submission

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `_id` | `old_id` | CharField | MongoDBのIDを文字列として保持 |
| `submitterAnonId` / `authorId` | `author` (FK) | ForeignKey | Userを`display_id`で検索 |
| `imageUrl` / `image` | `image` | ImageField | 画像URL |
| `caption` / `aim` | `caption` | TextField | キャプション |
| `commentEnabled` | `comment_enabled` | BooleanField | コメント有効フラグ |
| `status` | `status` | CharField | PUBLIC/PRIVATE/FLAGGED |
| `deleted` / `isDeleted` | `deleted_at` | DateTimeField | 削除フラグ→削除日時 |
| `deletedAt` | `deleted_at` | DateTimeField | 削除日時 |
| `deleteReason` | `delete_reason` | TextField | 削除理由 |
| `createdAt` | `created_at` | DateTimeField | 作成日時 |

**注意事項:**
- `deleted`フラグが`true`の場合、`deletedAt`が未設定なら現在時刻を設定
- ソフトデリート対応

### reactions → Reaction

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `submissionId` | `submission` (FK) | ForeignKey | Submissionを`old_id`で検索 |
| `userId` / `anonId` | `user` (FK) | ForeignKey | Userを`display_id`で検索 |
| `type` | `type` | CharField | `submit_medal`に固定 |
| - | `created_at` | DateTimeField | 現在時刻 |

**注意事項:**
- reactionsが別コレクションの場合と、submissionsに埋め込まれている場合の両方に対応
- `likes[]`配列からも抽出可能

### cards → Card

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `_id` | `old_id` | CharField | MongoDBのIDを文字列として保持 |
| `code` / `id` | `code` | CharField | カードコード（ユニーク） |
| `rarity` | `rarity` | CharField | common/rare/seasonal/special |

### userMeta.cardsAlbum → UserCard

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `cardsAlbum[].code` / `cardsAlbum[].id` | `card` (FK) | ForeignKey | Cardを`code`で検索 |
| `cardsAlbum[].obtainedAt` | `obtained_at` | DateTimeField | 獲得日時 |
| `anonId` | `user` (FK) | ForeignKey | Userを`display_id`で検索 |
| - | `obtained_at` | DateTimeField | 未設定時は現在時刻 |

**注意事項:**
- `userMeta.cardsAlbum`配列から各カードを抽出
- Cardが存在しない場合は自動作成（rarity='common'）

### jackpotWins → JackpotWin

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `_id` | `old_id` | CharField | MongoDBのIDを文字列として保持 |
| `userId` / `anonId` | `user` (FK) | ForeignKey | Userを`display_id`で検索 |
| `submissionId` | `submission` (FK) | ForeignKey | Submissionを`old_id`で検索（任意） |
| `wonAt` / `createdAt` | `won_at` | DateTimeField | 当選日時 |
| `pinnedUntil` | `pinned_until` | DateTimeField | ピン固定期限 |
| - | `pinned_until` | DateTimeField | 未設定時は`won_at + 24時間` |

**注意事項:**
- `pinned_until`が未設定の場合、`won_at + 24時間`をデフォルト値として設定

### discordShares → DiscordShare

| MongoDB フィールド | PostgreSQL フィールド | 型 | 備考 |
|-------------------|---------------------|-----|------|
| `_id` | `old_id` | CharField | MongoDBのIDを文字列として保持 |
| `userId` / `anonId` | `user` (FK) | ForeignKey | Userを`display_id`で検索 |
| `submissionId` | `submission` (FK) | ForeignKey | Submissionを`old_id`で検索（任意） |
| `channel` / `shareChannel` | `share_channel` | CharField | シェアチャンネル |
| `messageId` | `message_id` | CharField | DiscordメッセージID |
| `sharedAt` / `createdAt` | `shared_at` | DateTimeField | シェア日時 |

## 監査ログ

移行時に以下の監査ログを記録：

- **Action**: `EDIT_PROFILE`（または新規`IMPORT`アクション）
- **actor**: `None`（システム）
- **target_user**: 移行対象のユーザー
- **payload**: `{'action': 'IMPORT', 'old_id': '<mongo_id>'}`

## 使用方法

### Django管理コマンド

```bash
# ドライラン（テスト）
python manage.py load_legacy --dry-run

# 全コレクションを移行
python manage.py load_legacy

# 特定のコレクションのみ移行
python manage.py load_legacy --collection users

# チャンク投入（100件ずつ）
python manage.py load_legacy --limit 100 --offset 0
python manage.py load_legacy --limit 100 --offset 100

# MongoDB接続情報を指定
python manage.py load_legacy --mongo-uri mongodb://localhost:27017/ --mongo-db toybox
```

### 直接スクリプト実行

```bash
cd backend
python scripts/mongo_to_pg.py --mongo-uri mongodb://localhost:27017/ --mongo-db toybox --dry-run
```

## エラーハンドリング

- ユーザーが見つからない場合: スキップしてエラーログに記録
- 外部キー参照エラー: エラーログに記録して続行
- 重複データ: `get_or_create`で既存データを更新

## 注意事項

1. **順序**: users → userMeta → submissions → reactions → cards → jackpotWins → discordShares の順で実行推奨
2. **トランザクション**: 各コレクションごとにトランザクション処理（必要に応じて）
3. **バックアップ**: 移行前にPostgreSQLのバックアップを取得
4. **検証**: ドライランで移行内容を確認してから本番実行

