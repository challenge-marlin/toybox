# プロフィール設定のデバッグ手順

プロフィール設定が反映されない問題をデバッグする手順です。

## 1. ブラウザの開発者ツールで確認

1. **プロフィール設定ページ**（`http://localhost:8000/profile/`）を開く
2. **F12**キーで開発者ツールを開く
3. **Console**タブを開く
4. 表示名とプロフィール文を入力して「変更を保存してマイページへ」をクリック
5. コンソールに以下のログが表示されるはずです：
   - `Saving profile: { displayName: "...", bio: "..." }`
   - `Profile update response status: 200`（成功の場合）
   - `Profile update response data: { ... }`

## 2. ネットワークタブで確認

1. **Network**タブを開く
2. プロフィールを保存
3. `/api/user/profile/`へのPATCHリクエストを確認
4. **Request Payload**を確認：
   ```json
   {
     "displayName": "...",
     "bio": "..."
   }
   ```
5. **Response**を確認：
   ```json
   {
     "display_id": "...",
     "display_name": "...",
     "bio": "...",
     ...
   }
   ```

## 3. マイページで確認

1. **マイページ**（`http://localhost:8000/me/`）を開く
2. **Console**タブで以下のログを確認：
   - `Profile data received: { ... }`
   - `Set profile name to: ...`
   - `Set profile bio to: ...`

## 4. データベースで確認

Dockerコンテナ内でデータベースを確認：

```powershell
cd C:\github\toybox\backend
docker compose exec web python manage.py shell
```

シェルで実行：

```python
from users.models import UserMeta, User
from django.contrib.auth import get_user_model

User = get_user_model()

# 全てのユーザーのメタデータを確認
for meta in UserMeta.objects.all():
    print(f"User: {meta.user.display_id}")
    print(f"  display_name: {meta.display_name}")
    print(f"  bio: {meta.bio}")
    print()
```

## 5. APIエンドポイントを直接テスト

PowerShellで：

```powershell
# JWTトークンを取得（ログイン後）
$token = "your-jwt-token-here"

# プロフィール更新
Invoke-RestMethod -Uri "http://localhost:8000/api/user/profile/" `
  -Method PATCH `
  -Headers @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
  } `
  -Body (@{
    displayName = "テスト表示名"
    bio = "テストプロフィール文"
  } | ConvertTo-Json)

# プロフィール取得
Invoke-RestMethod -Uri "http://localhost:8000/api/user/profile/YOUR_ANON_ID/" `
  -Method GET `
  -Headers @{
    "Authorization" = "Bearer $token"
  }
```

## よくある問題

1. **JWTトークンが無効**
   - ログアウトして再度ログイン
   - トークンが期限切れの可能性

2. **データベースに保存されていない**
   - マイグレーションが実行されていない
   - `display_name`フィールドが存在しない

3. **APIエンドポイントが間違っている**
   - `/api/user/profile/`（PATCH）で更新
   - `/api/user/profile/<anonId>/`（GET）で取得

4. **キャッシュの問題**
   - ブラウザのキャッシュをクリア
   - 強制リロード（Ctrl+F5）

