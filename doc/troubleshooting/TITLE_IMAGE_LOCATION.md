# 称号画像の保存場所

## 保存場所

称号画像は以下のディレクトリに保存してください：

```
backend/public/uploads/titles/
```

## ファイル名の形式

ファイル名は**称号名.png**の形式で保存してください。

例：
- `蒸気の旅人.png`
- `真鍮の探究者.png`
- `歯車の達人.png`
- `工房の匠.png`

## 画像の推奨サイズ

- **推奨サイズ**: 321×115px
- **形式**: PNG（推奨）、JPEG、WebP
- **アスペクト比**: 約2.79:1

## 設定方法

### 方法1: ファイルを直接配置する場合

1. 画像ファイルを`backend/public/uploads/titles/`ディレクトリに配置
2. ファイル名を称号名と同じにする（例: `蒸気の旅人.png`）
3. Django管理画面または`init_titles`コマンドで`image_url`を設定

### 方法2: Django管理画面からアップロードする場合

1. Django管理画面（`/admin/gamification/title/`）にアクセス
2. 称号を選択または新規作成
3. 「バナー画像」フィールドから画像をアップロード
   - 自動的に`backend/public/uploads/titles/`に保存されます

### 方法3: image_urlフィールドを使用する場合

1. Django管理画面で称号を編集
2. 「画像URL」フィールドに`/uploads/titles/{称号名}.png`を入力
   - 例: `/uploads/titles/蒸気の旅人.png`

## 現在の称号一覧

以下の称号が定義されています：

- 蒸気の旅人
- 真鍮の探究者
- 歯車の達人
- 工房の匠
- 鉄と蒸気の詩人
- 火花をまとう見習い
- 真夜中の機巧設計士
- 歯車仕掛けの物語紡ぎ
- 蒸気都市の工房守

## 既存の画像ファイル

現在、以下の画像ファイルが`backend/public/uploads/titles/`に存在しています：

- 工房の匠.png
- 歯車の達人.png
- 歯車仕掛けの物語紡ぎ.png
- 火花をまとう見習い.png
- 蒸気の旅人.png
- 蒸気都市の工房守.png
- 真夜中の機巧設計士.png
- 真鍮の探究者.png
- 鉄と蒸気の詩人.png

## 画像URLの設定を自動化する

`init_titles`コマンドを実行すると、`backend/public/uploads/titles/`ディレクトリ内の画像ファイルを自動的に検出して、`image_url`を設定します：

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py init_titles
```

## アクセスURL

画像は以下のURLでアクセスできます：

```
/uploads/titles/{称号名}.png
```

例：
- `http://localhost:8000/uploads/titles/蒸気の旅人.png`
- `http://localhost:8000/uploads/titles/真鍮の探究者.png`

## 注意事項

1. **ファイル名の文字エンコーディング**: 日本語のファイル名を使用する場合、UTF-8エンコーディングで保存してください
2. **大文字小文字**: ファイル名は称号名と完全に一致させる必要があります
3. **拡張子**: `.png`、`.jpg`、`.jpeg`、`.webp`が使用可能です
4. **画像の優先順位**: 
   - `image`フィールド（Django管理画面からアップロード）が最優先
   - `image_url`フィールドが次に優先
   - どちらも設定されていない場合は画像が表示されません

## トラブルシューティング

### 画像が表示されない場合

1. ファイルが正しい場所に存在するか確認：
   ```powershell
   Test-Path backend\public\uploads\titles\{称号名}.png
   ```

2. ファイル名が称号名と完全に一致しているか確認

3. Django管理画面で`image_url`が正しく設定されているか確認

4. サーバーを再起動してメディアファイルの設定を反映

5. ブラウザの開発者ツール（F12）で画像URLが正しく生成されているか確認
