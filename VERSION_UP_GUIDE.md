# バージョンアップガイド

## 実装内容

以下の3つの機能を実装しました：

1. **プロフィール設定でヘッダー・アイコンの削除機能**
2. **ハッシュタグで人気ハッシュタグをサジェスト表示**
3. **ハッシュタグの大文字小文字統一（すべて小文字で表示）**

## WinSCPでのデプロイ手順

### 1. WinSCPでサーバーに接続

1. WinSCPを起動
2. 保存済みのサイトを選択（例: `toybox-server`）
3. 「ログイン」をクリック
4. パスワードを入力（初回のみ、または公開鍵認証が設定されていない場合）

### 2. ファイルをアップロード

#### 2.1. バックエンドファイルのアップロード

**ローカル側（左側）**: `C:\github\toybox\backend\`
**サーバー側（右側）**: `/home/app/toybox/backend/`

アップロードするファイル：
- `backend/users/views.py` - プロフィール削除API
- `backend/submissions/views.py` - ハッシュタグAPI（小文字統一）
- `backend/lottery/services.py` - ハッシュタグ保存時の小文字統一
- `backend/frontend/templates/frontend/profile.html` - プロフィール設定ページ
- `backend/frontend/templates/frontend/me.html` - 投稿ページ（ハッシュタグサジェスト）
- `backend/frontend/templates/frontend/feed.html` - フィードページ（ハッシュタグ表示の小文字統一）
- `backend/frontend/static/frontend/js/pages/profile.js` - プロフィール設定JS

**手順**:
1. 左側でファイルを選択
2. 右側で対応するディレクトリに移動
3. ファイルをドラッグ&ドロップでアップロード
4. 上書き確認ダイアログで「はい」をクリック

#### 2.2. データベースマイグレーション（不要）

今回の変更は既存のデータベース構造を変更していないため、マイグレーションは不要です。

### 3. サーバーを再起動

WinSCPのターミナル機能を使用するか、SSH接続で：

```bash
# Djangoサーバーを再起動（systemdを使用している場合）
sudo systemctl restart toybox-backend

# または、手動で実行している場合
# プロセスを停止してから再起動
```

### 4. 確認

1. ブラウザでアプリケーションにアクセス
2. 各機能が正しく動作するか確認：
   - プロフィール設定ページでヘッダー・アイコンの削除ボタンが表示される
   - 投稿ページでハッシュタグ入力時にサジェストが表示される
   - ハッシュタグがすべて小文字で表示される

## 実装詳細

### 1. プロフィール設定でヘッダー・アイコンの削除機能

#### 変更ファイル
- `backend/users/views.py`: `ProfileUploadView`に`delete`メソッドを追加
- `backend/frontend/templates/frontend/profile.html`: 削除ボタンを追加
- `backend/frontend/static/frontend/js/pages/profile.js`: 削除機能のJavaScriptを追加

#### 機能
- ヘッダー画像とアバター画像を個別に削除可能
- 削除ボタンは画像が設定されている場合のみ表示
- 削除後は自動的にプロフィール情報を再読み込み

### 2. ハッシュタグで人気ハッシュタグをサジェスト表示

#### 変更ファイル
- `backend/frontend/templates/frontend/me.html`: サジェスト機能を追加

#### 機能
- ハッシュタグ入力時に、入力内容に一致する人気ハッシュタグをサジェスト表示
- 入力から300ms後にサジェストを表示（デバウンス処理）
- サジェストアイテムをクリックすると、そのハッシュタグが入力欄に設定される
- 最大5件のサジェストを表示

### 3. ハッシュタグの大文字小文字統一

#### 変更ファイル
- `backend/submissions/views.py`: ハッシュタグAPIとフィルタリング処理で小文字に統一
- `backend/lottery/services.py`: ハッシュタグ保存時に小文字に統一
- `backend/frontend/templates/frontend/me.html`: 入力時に小文字に変換、保存時に小文字に統一
- `backend/frontend/templates/frontend/feed.html`: 表示時に小文字に統一

#### 機能
- ハッシュタグの入力時に自動的に小文字に変換
- 保存時にすべて小文字に統一
- 表示時にすべて小文字で表示
- フィルタリング時も小文字で比較

## 注意事項

1. **バックアップ**: 重要なファイルをアップロードする前に、サーバー側のファイルをバックアップしてください
2. **権限**: ファイルの権限が正しく設定されているか確認してください
3. **ログ**: エラーが発生した場合は、サーバーログを確認してください

## トラブルシューティング

### ファイルがアップロードできない場合

1. ファイルの権限を確認
2. ディスク容量を確認
3. SSH接続が正常か確認

### サーバーが起動しない場合

1. ログファイルを確認：
   ```bash
   tail -f /home/app/toybox/backend/logs/django.log
   ```
2. 構文エラーがないか確認：
   ```bash
   python manage.py check
   ```

### 機能が動作しない場合

1. ブラウザのキャッシュをクリア
2. 開発者ツール（F12）のコンソールでエラーを確認
3. サーバーログを確認
