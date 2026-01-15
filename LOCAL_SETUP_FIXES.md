# ローカル環境での修正手順

## 問題1: 称号画像が表示されない

### 原因
称号画像のURL生成が統一されていませんでした。

### 修正内容
`backend/users/views.py`の称号画像URL生成を`get_image_url`関数を使うように統一しました。

### 確認方法
1. サーバーを再起動してください
2. プロフィールページで称号画像が表示されるか確認してください

## 問題2: カード名がIDで表示される

### 原因
データベースにカードマスタデータがロードされていない可能性があります。

### 解決方法

#### ステップ1: カードマスタデータをロード

PowerShellで、プロジェクトの`backend`ディレクトリに移動して以下を実行：

**方法A: 仮想環境を使用する場合（推奨）**

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py load_card_master
```

**方法B: pyランチャーを使用する場合**

```powershell
cd backend
py manage.py load_card_master
```

**方法C: TSVファイルのパスを指定する場合**

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py load_card_master --tsv-file src/data/card_master.tsv
```

**注意**: PowerShellで仮想環境をアクティベートする際、実行ポリシーのエラーが出る場合は、以下を実行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### ステップ2: データベースのカード情報を確認

Django管理画面またはシェルで確認：

```powershell
python manage.py shell
```

```python
from gamification.models import Card
Card.objects.count()  # カード数が0でないことを確認
Card.objects.first()  # カード名が設定されていることを確認
```

#### ステップ3: 既存のカードデータを更新（必要に応じて）

既存のカードデータに名前が設定されていない場合、以下のコマンドで更新できます：

```powershell
python manage.py load_card_master
```

このコマンドは既存のカードも更新します。

### 修正内容
`backend/gamification/views.py`の`MyCardsView`で、カード名が空の場合にカードマスタから取得するフォールバック処理を追加しました。

## 確認手順

### 1. サーバーを再起動

```powershell
# バックエンドサーバーを再起動
cd backend
python manage.py runserver
```

### 2. ブラウザで確認

1. `/collection`ページでカード名が正しく表示されるか確認
2. `/me`ページで称号画像が表示されるか確認
3. プロフィールページで称号画像が表示されるか確認

### 3. ブラウザの開発者ツールで確認

1. F12キーで開発者ツールを開く
2. 「Network」タブを開く
3. `/api/gamification/me/`エンドポイントのレスポンスを確認
   - `entries[].meta.card_name`が正しく設定されているか確認
4. `/api/users/profile/{anonId}/`エンドポイントのレスポンスを確認
   - `activeTitleImageUrl`が正しく設定されているか確認

## トラブルシューティング

### カードマスタデータがロードされない場合

1. TSVファイルのパスを確認：
   ```powershell
   # backendディレクトリから
   Test-Path src/data/card_master.tsv
   ```

2. TSVファイルの形式を確認：
   - タブ区切り（TSV）であること
   - ヘッダー行が正しいこと（`card_id`, `card_name`, `rarity`, `image_url`）

3. データベース接続を確認：
   ```powershell
   python manage.py dbshell
   ```

### 称号画像が表示されない場合

1. 称号データが存在するか確認：
   ```powershell
   python manage.py shell
   ```
   ```python
   from gamification.models import Title
   Title.objects.all()  # 称号が存在するか確認
   Title.objects.first().image_url  # 画像URLが設定されているか確認
   ```

2. 画像ファイルが存在するか確認：
   - `backend/public/uploads/titles/`ディレクトリに画像ファイルがあるか確認
   - または、`image_url`フィールドに正しいURLが設定されているか確認

3. メディアファイルの設定を確認：
   - `settings.py`の`MEDIA_ROOT`と`MEDIA_URL`が正しく設定されているか確認
   - `urls.py`でメディアファイルの配信設定が正しいか確認

## 関連ファイル

- `backend/users/views.py` - プロフィールAPI（称号画像URL生成）
- `backend/gamification/views.py` - カード一覧API（カード名取得）
- `backend/gamification/services.py` - カードマスタデータロード
- `backend/gamification/management/commands/load_card_master.py` - カードマスタロードコマンド
- `backend/src/data/card_master.tsv` - カードマスタデータ（TSV形式）
