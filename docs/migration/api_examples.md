# ToyBox API Examples

## 一般API

### 認証

#### ログイン
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### トークンリフレッシュ
```bash
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### ヘルスチェック

```bash
GET /api/health/

Response:
{
  "status": "ok"
}
```

### 投稿

#### 投稿作成
```bash
POST /api/submissions/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

{
  "image": <file>,
  "caption": "今日の成果",
  "comment_enabled": true
}

Response:
{
  "id": 1,
  "author": 1,
  "author_display_id": "user123",
  "author_avatar_url": "/uploads/avatar.jpg",
  "image": "/uploads/submissions/image.jpg",
  "caption": "今日の成果",
  "comment_enabled": true,
  "status": "PUBLIC",
  "active_title": "蒸気の旅人",
  "title_color": "#FF5733",
  "reactions_count": 0,
  "user_reacted": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 当日フィード取得
```bash
GET /api/submissions/?day=today
Authorization: Bearer <access_token>

Response:
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "author": 1,
      "author_display_id": "user123",
      "author_avatar_url": "/uploads/avatar.jpg",
      "image": "/uploads/submissions/image.jpg",
      "caption": "今日の成果",
      "comment_enabled": true,
      "status": "PUBLIC",
      "active_title": "蒸気の旅人",
      "title_color": "#FF5733",
      "reactions_count": 5,
      "user_reacted": false,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### リアクション追加
```bash
POST /api/submissions/1/react/submit_medal/
Authorization: Bearer <access_token>

Response:
{
  "ok": true,
  "message": "Reaction added"
}
```

#### コメント有効/無効切り替え（投稿者のみ）
```bash
POST /api/submissions/1/comments/toggle/
Authorization: Bearer <access_token>

Response:
{
  "ok": true,
  "comment_enabled": false
}
```

### ユーザーメタデータ

```bash
GET /api/users/me/meta/
Authorization: Bearer <access_token>

Response:
{
  "active_title": "蒸気の旅人",
  "title_color": "#FF5733",
  "expires_at": "2024-01-08T12:00:00Z",
  "bio": "自己紹介文",
  "header_url": "/uploads/header.jpg",
  "lottery_bonus_count": 3
}
```

### 抽選

```bash
POST /api/lottery/draw/
Authorization: Bearer <access_token>

Response (当選時):
{
  "ok": true,
  "won": true,
  "jackpot_win_id": 1,
  "pinned_until": "2024-01-02T12:00:00Z"
}

Response (未当選時):
{
  "ok": true,
  "won": false,
  "probability": 0.012,
  "bonus_count": 4
}
```

## 管理API

### ユーザー管理

#### ユーザー一覧（検索）
```bash
GET /api/admin/users/?q=user@example.com
Authorization: Bearer <admin_token>

Response:
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "email": "user@example.com",
      "display_id": "user123",
      "role": "USER",
      "avatar_url": "/uploads/avatar.jpg",
      "is_suspended": false,
      "banned_at": null,
      "warning_count": 0,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### ユーザー詳細
```bash
GET /api/admin/users/1/
Authorization: Bearer <admin_token>

Response:
{
  "id": 1,
  "email": "user@example.com",
  "display_id": "user123",
  "role": "USER",
  "avatar_url": "/uploads/avatar.jpg",
  "is_suspended": false,
  "banned_at": null,
  "warning_count": 0,
  "warning_notes": null,
  "meta": {
    "active_title": "蒸気の旅人",
    "title_color": "#FF5733",
    "expires_at": "2024-01-08T12:00:00Z",
    "lottery_bonus_count": 3
  },
  "registration": {
    "address": "東京都...",
    "age_group": "20代",
    "phone": "090-1234-5678"
  },
  "cards_count": 15,
  "submissions_count": 42,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### 警告発行
```bash
POST /api/admin/users/1/warn/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "message": "不適切な投稿を削除しました"
}

Response:
{
  "ok": true,
  "warning_count": 1
}
```

#### 停止
```bash
POST /api/admin/users/1/suspend/
Authorization: Bearer <admin_token>

Response:
{
  "ok": true
}
```

#### 停止解除
```bash
POST /api/admin/users/1/unsuspend/
Authorization: Bearer <admin_token>

Response:
{
  "ok": true
}
```

#### BAN
```bash
POST /api/admin/users/1/ban/
Authorization: Bearer <admin_token>

Response:
{
  "ok": true
}
```

#### BAN解除
```bash
POST /api/admin/users/1/unban/
Authorization: Bearer <admin_token>

Response:
{
  "ok": true
}
```

#### パスワードリセット
```bash
POST /api/admin/users/1/reset_password/
Authorization: Bearer <admin_token>

Response:
{
  "ok": true,
  "temp_password": "abc123xyz789"  # 本番ではメール送信
}
```

### 投稿管理

#### 投稿一覧（削除済み含む）
```bash
GET /api/admin/submissions/?include_deleted=true
Authorization: Bearer <admin_token>

Response:
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "author": 1,
      "author_email": "user@example.com",
      "author_display_id": "user123",
      "image": "/uploads/submissions/image.jpg",
      "caption": "投稿内容",
      "comment_enabled": true,
      "status": "PUBLIC",
      "deleted_at": null,
      "delete_reason": null,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### ソフトデリート
```bash
POST /api/admin/submissions/1/delete/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "不適切な内容"
}

Response:
{
  "ok": true
}
```

#### 復元
```bash
POST /api/admin/submissions/1/restore/
Authorization: Bearer <admin_token>

Response:
{
  "ok": true
}
```

### Discordシェア履歴

```bash
GET /api/admin/discord-shares/?user=1
Authorization: Bearer <admin_token>

Response:
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "user": 1,
      "user_email": "user@example.com",
      "user_display_id": "user123",
      "submission": 1,
      "submission_id": 1,
      "share_channel": "general",
      "message_id": "123456789",
      "shared_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### 監査ログ

```bash
GET /api/admin/audit-logs/?user=1
Authorization: Bearer <admin_token>

Response:
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "actor": 2,
      "actor_email": "admin@example.com",
      "actor_display_id": "admin",
      "target_user": 1,
      "target_user_email": "user@example.com",
      "target_user_display_id": "user123",
      "target_submission": null,
      "action": "WARN",
      "payload": {
        "message": "不適切な投稿を削除しました",
        "warning_count": 1
      },
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

