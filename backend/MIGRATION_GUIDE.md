# ToyBox Django RDB Migration Guide

## MongoDB → PostgreSQL マイグレーション手順

### 1. マイグレーションファイルの生成

```bash
# 各アプリのマイグレーションを生成
python manage.py makemigrations users
python manage.py makemigrations gamification
python manage.py makemigrations submissions
python manage.py makemigrations lottery
python manage.py makemigrations sharing
python manage.py makemigrations adminpanel
```

### 2. マイグレーションの実行

```bash
# すべてのマイグレーションを実行
python manage.py migrate
```

### 3. カスタムインデックスの追加（PostgreSQL関数インデックス）

JackpotWinモデルの`won_at::date`インデックスは、マイグレーション後に手動で追加する必要があります：

```sql
-- PostgreSQLで実行
CREATE INDEX jackpot_wins_won_at_date_idx ON jackpot_wins ((won_at::date));
```

または、Djangoマイグレーションで追加する場合：

```python
# lottery/migrations/XXXX_add_date_index.py
from django.db import migrations
from django.db.models import Index

class Migration(migrations.Migration):
    dependencies = [
        ('lottery', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS jackpot_wins_won_at_date_idx ON jackpot_wins ((won_at::date));",
            reverse_sql="DROP INDEX IF EXISTS jackpot_wins_won_at_date_idx;"
        ),
    ]
```

### 4. データ移行（ETL）

既存のMongoDBデータをPostgreSQLに移行する場合：

1. MongoDBからデータをエクスポート
2. `old_id`フィールドにMongoDBの`_id`を保存
3. リレーションシップを再構築（`anon_id` → `User.id`など）

### 5. モデル構造の確認

#### users.models
- `User`: email unique, password, display_id, role, avatar_url, is_suspended, banned_at, warning_count, warning_notes
- `UserRegistration`: 任意のプロフィールフィールド
- `UserMeta`: OneToOne User, active_title, title_color, expires_at
- `UserCard`: user FK, card FK, obtained_at, unique(user, card)

#### gamification.models
- `Title`: name, color, duration_days default 7
- `Card`: code unique, rarity

#### submissions.models
- `Submission`: author FK User, image, caption, comment_enabled, status, created_at, deleted_at, delete_reason (ソフトデリート)
- `Reaction`: type, user FK, submission FK, unique(user, submission, type)

#### lottery.models
- `LotteryRule`: base_rate, per_submit_increment, max_rate, daily_cap
- `JackpotWin`: user FK, submission FK null, won_at, pinned_until

#### sharing.models
- `DiscordShare`: user FK, submission FK null, shared_at, share_channel, message_id

#### adminpanel.models
- `AdminAuditLog`: actor FK User, target_user FK User null, target_submission FK Submission null, action, payload JSON, created_at

### 6. インデックス

- Submission: `created_at desc`, `deleted_at`
- UserMeta: `expires_at`
- JackpotWin: `won_at`, `won_at::date` (関数インデックス)
- DiscordShare: `shared_at`
- AdminAuditLog: `created_at`

### 7. シグナル

- User/Submission/DiscordShare/処分系操作の変更時にAdminAuditLogを自動記録
- `adminpanel/signals.py`で実装済み

### 8. ソフトデリート

Submissionモデルには`soft_delete()`と`restore()`メソッドを実装済み。

```python
# ソフトデリート
submission.soft_delete(reason="違反行為")

# 復元
submission.restore()
```

### 9. クエリでのソフトデリート除外

```python
# 削除されていない投稿のみ取得
Submission.objects.filter(deleted_at__isnull=True)

# 削除された投稿も含めて取得
Submission.objects.all()
```
