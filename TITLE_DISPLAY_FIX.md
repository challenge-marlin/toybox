# 称号表示の問題を解決

## 実施した修正

### 1. 画像URL生成の修正

**問題**: `get_image_url`関数で`verify_exists=True`を指定していたため、ファイルが存在しない場合に`None`が返されていました。

**修正内容**:
- `backend/users/views.py`の`ProfileGetView`で`verify_exists=False`に変更
- `backend/users/serializers.py`の`UserMetaSerializer`で`verify_exists=False`に変更

これにより、ファイルが存在しなくてもURLが返されるようになり、フロントエンドで画像読み込みエラー時にフォールバック表示が機能します。

### 2. デバッグログの追加

フロントエンドにデバッグログを追加し、APIから返される称号データを確認できるようにしました。

## 確認手順

### 1. サーバーを再起動

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

### 2. ブラウザで確認

1. `/me`ページにアクセス
2. ブラウザの開発者ツール（F12）を開く
3. 「Console」タブで以下のログを確認：
   ```
   Title data: {
     activeTitle: "...",
     activeTitleUntil: "...",
     activeTitleImageUrl: "...",
     active_title_image_url: "..."
   }
   ```

### 3. 称号が表示されない場合の確認項目

#### 3.1. ユーザーに称号が付与されているか確認

Django管理画面またはシェルで確認：

```powershell
python manage.py shell
```

```python
from users.models import UserMeta
from django.contrib.auth import get_user_model

User = get_user_model()
# ユーザーを取得（例: display_idが"testuser"の場合）
user = User.objects.get(display_id="testuser")
meta = UserMeta.objects.get(user=user)
print(f"Active Title: {meta.active_title}")
print(f"Expires At: {meta.expires_at}")
```

#### 3.2. 称号データが存在するか確認

```python
from gamification.models import Title
Title.objects.all()  # すべての称号を表示
Title.objects.first().image_url  # 画像URLを確認
```

#### 3.3. 画像ファイルが存在するか確認

```powershell
# 称号名が「蒸気の旅人」の場合
Test-Path backend\public\uploads\titles\蒸気の旅人.png
```

#### 3.4. APIレスポンスを確認

ブラウザの開発者ツールの「Network」タブで：
1. `/api/user/profile/{anonId}/`エンドポイントのレスポンスを確認
2. `activeTitle`と`activeTitleImageUrl`が正しく設定されているか確認

## よくある問題と解決方法

### 問題1: 称号が付与されていない

**解決方法**: 投稿をして称号を獲得するか、Django管理画面で手動で称号を付与：

```python
from users.models import UserMeta
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
user = User.objects.get(display_id="testuser")
meta = UserMeta.objects.get(user=user)
meta.active_title = "蒸気の旅人"
meta.expires_at = timezone.now() + timedelta(days=7)
meta.save()
```

### 問題2: 称号の有効期限が切れている

**解決方法**: 有効期限を延長：

```python
from users.models import UserMeta
from django.utils import timezone
from datetime import timedelta

meta = UserMeta.objects.get(user=user)
meta.expires_at = timezone.now() + timedelta(days=7)
meta.save()
```

### 問題3: 画像URLが設定されていない

**解決方法**: `init_titles`コマンドを実行：

```powershell
python manage.py init_titles
```

または、Django管理画面で手動で設定：
1. `/admin/gamification/title/`にアクセス
2. 称号を選択
3. 「画像URL」フィールドに`/uploads/titles/{称号名}.png`を設定

### 問題4: 画像ファイルが存在しない

**解決方法**: 画像ファイルを`backend/public/uploads/titles/`ディレクトリに配置

## 修正後の動作

1. **画像が存在する場合**: 画像が表示されます
2. **画像が存在しない場合**: 画像読み込みエラー時に、称号名がテキストで表示されます
3. **称号が存在しない場合**: 何も表示されません（正常な動作）

## 関連ファイル

- `backend/users/views.py` - ProfileGetView（プロフィールAPI）
- `backend/users/serializers.py` - UserMetaSerializer（ユーザーメタシリアライザー）
- `backend/toybox/image_utils.py` - get_image_url関数（画像URL生成）
- `backend/frontend/templates/frontend/me.html` - フロントエンド表示ロジック
