# Discord OAuth2設定ガイド

## 1. Discord Developer Portalでの設定

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. アプリケーションを選択（または新規作成）
3. 「OAuth2」タブを開く
4. 「Redirects」セクションに以下のリダイレクトURIを追加：

### 開発環境の場合
```
http://localhost:8000/api/auth/discord/callback/
```

### 本番環境の場合
```
https://yourdomain.com/api/auth/discord/callback/
```

**重要**: 
- 末尾のスラッシュ（`/`）を含める
- `http://` または `https://` で始める
- 完全なURLを指定する（相対パスは不可）
- **リダイレクトURIは、実際にアプリケーションが使用するURLと完全に一致させる必要があります**

### 実際のリダイレクトURIの確認方法

アプリケーションはリクエストから自動的にリダイレクトURIを生成します。実際に生成されるURIを確認するには：

1. アプリケーションを起動
2. `/api/auth/discord/login/`にアクセス
3. ログを確認（`Discord OAuth redirect URI:`で始まる行）
4. Discord Developer Portalに、ログに表示されたURIを追加

## 2. 環境変数の設定

`.env`ファイルまたは環境変数に以下を設定：

```bash
# Discord OAuth2設定
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:8000/api/auth/discord/callback/
```

**重要**: 
- `DISCORD_REDIRECT_URI`は、Discord Developer Portalで設定したものと**完全に一致**させる必要があります
- 末尾のスラッシュ（`/`）を含める
- 開発環境と本番環境で異なる場合は、それぞれ設定する
- **注意**: アプリケーションはリクエストから自動的にリダイレクトURIを生成するため、環境変数の`DISCORD_REDIRECT_URI`はフォールバックとして使用されます。通常は設定不要ですが、動的生成が失敗した場合に使用されます。

## 3. 確認方法

1. 環境変数が正しく設定されているか確認：
   ```bash
   docker compose exec web python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.DISCORD_CLIENT_ID)
   >>> print(settings.DISCORD_REDIRECT_URI)
   ```

2. Discord Developer Portalの「OAuth2」タブで、リダイレクトURIが正しく登録されているか確認

3. ブラウザで `/api/auth/discord/login/` にアクセスして、エラーが出ないか確認

## 4. よくあるエラー

### "redirect_uri が無効です"
- Discord Developer Portalで設定したリダイレクトURIと、実際に生成されるリダイレクトURIが一致していない
- 末尾のスラッシュ（`/`）の有無が異なる
- `http://` と `https://` が異なる
- ポート番号が異なる（例: `localhost:8000` vs `127.0.0.1:8000`）

**解決方法**:
1. アプリケーションのログを確認して、実際に生成されているリダイレクトURIを確認
2. Discord Developer Portalの「OAuth2」タブで、そのURIが登録されているか確認
3. 登録されていない場合は追加
4. 複数のバリエーション（`localhost`と`127.0.0.1`など）を登録することも可能

### "Invalid client"
- `DISCORD_CLIENT_ID`が正しく設定されていない
- Discord Developer Portalで確認

### "Invalid client secret"
- `DISCORD_CLIENT_SECRET`が正しく設定されていない
- Discord Developer Portalで「Reset Secret」を実行した場合は、新しいシークレットを設定する


