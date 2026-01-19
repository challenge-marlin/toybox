# SSO 502エラー修正 - WinSCPアップロードファイルリスト

## アップロードが必要なファイル

以下の3つのファイルをWinSCPでアップロードしてください。

### ローカル側のパス
`C:\github\toybox\backend\`

### サーバー側のパス
`/home/app/toybox/backend/` または `/path/to/toybox/backend/`

---

## アップロードするファイル一覧

### 1. SSOサービス層の修正
**ローカル**: `backend/sso_integration/services.py`  
**サーバー**: `/home/app/toybox/backend/sso_integration/services.py`

**変更内容**:
- SSO APIタイムアウトを5秒 → 30秒に延長
- エラーハンドリングを改善（タイムアウトエラーと接続エラーを個別に処理）
- より詳細なログを記録

### 2. SSOビュー層の修正
**ローカル**: `backend/sso_integration/views.py`  
**サーバー**: `/home/app/toybox/backend/sso_integration/views.py`

**変更内容**:
- すべての例外をキャッチして適切に処理
- ログレベルを`warning`から`error`に変更し、詳細ログを記録
- ユーザー向けエラーメッセージを改善

### 3. nginx設定の修正
**ローカル**: `backend/nginx/conf/default.conf`  
**サーバー**: `/home/app/toybox/backend/nginx/conf/default.conf`

**変更内容**:
- `proxy_read_timeout` を60秒 → 90秒に延長
- SSO処理に時間がかかる場合に対応

---

## WinSCPでのアップロード手順

### ステップ1: WinSCPでサーバーに接続

1. WinSCPを起動
2. 保存済みのサイトを選択（例: `toybox-server`）
3. 「ログイン」をクリック
4. パスワードを入力（必要に応じて）

### ステップ2: ファイルをアップロード

#### 方法A: 個別にアップロード

1. **左側（ローカル）**: `C:\github\toybox\backend\sso_integration\`
2. **右側（サーバー）**: `/home/app/toybox/backend/sso_integration/`
3. `services.py` と `views.py` を選択してドラッグ&ドロップ
4. 上書き確認ダイアログで「はい」をクリック

1. **左側（ローカル）**: `C:\github\toybox\backend\nginx\conf\`
2. **右側（サーバー）**: `/home/app/toybox/backend/nginx/conf/`
3. `default.conf` を選択してドラッグ&ドロップ
4. 上書き確認ダイアログで「はい」をクリック

#### 方法B: ディレクトリごとアップロード

1. **左側（ローカル）**: `C:\github\toybox\backend\`
2. **右側（サーバー）**: `/home/app/toybox/backend/`
3. 以下のディレクトリ/ファイルを選択：
   - `sso_integration/services.py`
   - `sso_integration/views.py`
   - `nginx/conf/default.conf`
4. ドラッグ&ドロップでアップロード
5. 上書き確認ダイアログで「はい」をクリック

---

## アップロード後の作業

### ステップ3: Dockerコンテナを再起動

WinSCPのターミナル機能を使用するか、SSH接続で：

```bash
# プロジェクトディレクトリに移動
cd /home/app/toybox/backend

# Dockerコンテナを停止
docker compose down

# Dockerコンテナを再起動
docker compose up -d --build

# コンテナの状態を確認
docker compose ps

# webサービスのログを確認
docker compose logs web --tail=50
```

### ステップ4: 動作確認

1. **ヘルスチェックエンドポイントを確認**
   ```bash
   curl http://localhost:8000/api/health/
   ```

2. **SSO処理をテスト**
   - ブラウザでSSOログインを試行
   - エラーが発生しないか確認

3. **ログを確認**
   ```bash
   docker compose logs web | grep -i "sso\|SSO" | tail -20
   ```

---

## 注意事項

1. **バックアップ**: アップロード前に、サーバー側の既存ファイルをバックアップしてください
   ```bash
   # サーバー側で実行
   cp /home/app/toybox/backend/sso_integration/services.py /home/app/toybox/backend/sso_integration/services.py.backup
   cp /home/app/toybox/backend/sso_integration/views.py /home/app/toybox/backend/sso_integration/views.py.backup
   cp /home/app/toybox/backend/nginx/conf/default.conf /home/app/toybox/backend/nginx/conf/default.conf.backup
   ```

2. **ファイル権限**: アップロード後、ファイルの権限が正しいか確認してください
   ```bash
   ls -la /home/app/toybox/backend/sso_integration/
   ls -la /home/app/toybox/backend/nginx/conf/
   ```

3. **nginx設定の反映**: nginx設定を変更した場合、nginxサービスを再起動する必要があります
   - Dockerコンテナを使用している場合: `docker compose restart nginx`（nginxサービスがある場合）
   - システムレベルのnginxの場合: `sudo systemctl restart nginx`

---

## トラブルシューティング

### ファイルがアップロードできない場合

1. **権限を確認**
   ```bash
   ls -la /home/app/toybox/backend/
   ```

2. **ディスク容量を確認**
   ```bash
   df -h
   ```

3. **SSH接続を確認**
   - WinSCPの接続ログを確認
   - 接続情報が正しいか確認（`WINSCP_CONNECTION_INFO.md`を参照）

### コンテナが起動しない場合

1. **ログを確認**
   ```bash
   docker compose logs web
   ```

2. **構文エラーを確認**
   ```bash
   docker compose exec web python manage.py check
   ```

3. **ファイルの内容を確認**
   ```bash
   cat /home/app/toybox/backend/sso_integration/services.py | head -20
   ```

---

## 参考資料

- `SSO_502_ERROR_FIX.md` - 詳細な診断手順とトラブルシューティング
- `WINSCP_DEPLOYMENT_GUIDE.md` - WinSCPでのデプロイ手順（一般）
- `WINSCP_CONNECTION_INFO.md` - WinSCP接続情報
