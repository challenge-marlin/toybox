# WinSCPでのデプロイ手順

## 前提条件

- WinSCPがインストールされていること
- SSH接続情報が設定されていること（`WINSCP_CONNECTION_INFO.md`を参照）

## デプロイ手順

### ステップ1: WinSCPでサーバーに接続

1. WinSCPを起動
2. 保存済みのサイトを選択（例: `toybox-server`）
3. 「ログイン」をクリック
4. パスワードを入力（初回のみ、または公開鍵認証が設定されていない場合）

### ステップ2: ファイルをアップロード

#### 2.1. バックエンドファイルのアップロード

**ローカル側（左側）**: `C:\github\toybox\backend\`
**サーバー側（右側）**: `/home/app/toybox/backend/`

アップロードするファイル：
- `backend/users/views.py` - プロフィール削除API
- `backend/users/serializers.py` - シリアライザー
- `backend/submissions/views.py` - ハッシュタグAPI
- `backend/frontend/templates/frontend/profile.html` - プロフィール設定ページ
- `backend/frontend/templates/frontend/me.html` - 投稿ページ（ハッシュタグサジェスト）
- `backend/frontend/static/frontend/js/pages/profile.js` - プロフィール設定JS

**手順**:
1. 左側でファイルを選択
2. 右側で対応するディレクトリに移動
3. ファイルをドラッグ&ドロップでアップロード
4. 上書き確認ダイアログで「はい」をクリック

#### 2.2. データベースマイグレーション（必要に応じて）

サーバー側でSSH接続またはWinSCPのターミナル機能を使用：

```bash
cd /home/app/toybox/backend
source venv/bin/activate  # 仮想環境をアクティベート
python manage.py migrate
```

### ステップ3: サーバーを再起動

WinSCPのターミナル機能を使用するか、SSH接続で：

```bash
# Djangoサーバーを再起動（systemdを使用している場合）
sudo systemctl restart toybox-backend

# または、手動で実行している場合
# プロセスを停止してから再起動
```

### ステップ4: 確認

1. ブラウザでアプリケーションにアクセス
2. 各機能が正しく動作するか確認

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
