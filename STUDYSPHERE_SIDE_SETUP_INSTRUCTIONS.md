# StudySphere側 SSO連携設定指示書

## 概要

TOYBOXとStudySphereのSSO連携を実現するため、StudySphere側で以下の設定と実装が必要です。

## 現在の問題

現在、StudySphere側の「TOYBOXへ」ボタンを押すと、以下のURLにアクセスしています：

```
https://studysphere.ayatori-inc.co.jp/sso-dispatch?target=toybox_prod
```

しかし、このURLがTOYBOX側の適切なコールバックURLにリダイレクトされていないため、チケットが付与されず、通常のログイン画面が表示されてしまいます。

## 必要な実装

### 1. SSOディスパッチエンドポイントの実装

StudySphere側の`/sso-dispatch?target=toybox_prod`エンドポイントで、以下の処理を実装してください：

1. **現在ログイン中のユーザー情報を取得**
   - StudySphereにログイン中のユーザーの`user_id`と`login_code`を取得

2. **SSOチケットを生成**
   - TOYBOX側のSSO APIを呼び出してチケットを生成
   - APIエンドポイント: `{SSO_API_BASE_URL}/api/sso/ticket/generate-by-logincode`
   - リクエスト例:
     ```json
     {
       "login_code": "ユーザーのログインコード",
       "target_system": "toybox_prod",
       "source_system": "studysphere",
       "context": "portal_click"
     }
     ```
   - レスポンス例:
     ```json
     {
       "success": true,
       "data": {
         "ticket": "生成されたチケット文字列"
       }
     }
     ```

3. **TOYBOX側のコールバックURLにリダイレクト**
   - 生成されたチケットを付与してTOYBOX側にリダイレクト
   - リダイレクトURL: `https://toybox.ayatori-inc.co.jp/sso/callback/?ticket={生成されたチケット}`

### 2. 実装例（疑似コード）

```python
# StudySphere側の実装例
def sso_dispatch(request, target_system):
    """
    SSOディスパッチエンドポイント
    target_system: 連携先システム（例: "toybox_prod"）
    """
    # 1. 現在ログイン中のユーザーを取得
    if not request.user.is_authenticated:
        return redirect('/login/')
    
    user = request.user
    login_code = user.login_code  # または適切なフィールド名
    
    # 2. TOYBOX側のSSO APIを呼び出してチケットを生成
    sso_api_url = "https://studysphere-api.ayatori-inc.co.jp/api/sso/ticket/generate-by-logincode"
    payload = {
        "login_code": login_code,
        "target_system": target_system,
        "source_system": "studysphere",
        "context": "portal_click"
    }
    
    # SSO_SERVICE_TOKENを使用して認証
    headers = {
        "Authorization": f"Bearer {SSO_SERVICE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(sso_api_url, json=payload, headers=headers)
    result = response.json()
    
    if not result.get("success"):
        # エラーハンドリング
        return redirect('/error/?message=SSO連携に失敗しました')
    
    ticket = result.get("data", {}).get("ticket")
    if not ticket:
        return redirect('/error/?message=チケットの生成に失敗しました')
    
    # 3. TOYBOX側のコールバックURLにリダイレクト
    toybox_callback_url = f"https://toybox.ayatori-inc.co.jp/sso/callback/?ticket={ticket}"
    return redirect(toybox_callback_url)
```

### 3. 必要な設定値

StudySphere側で以下の設定値が必要です：

- **TOYBOX側のコールバックURL**: `https://toybox.ayatori-inc.co.jp/sso/callback/`
- **SSO API ベースURL**: `https://studysphere-api.ayatori-inc.co.jp`（または適切なURL）
- **SSO_SERVICE_TOKEN**: StudySphere側で発行されたサービストークン
- **システムキー**: `toybox_prod`

## TOYBOX側の動作フロー

StudySphere側から正しくリダイレクトされた場合、TOYBOX側では以下のフローで動作します：

1. **`/sso/callback/?ticket=xxx`にアクセス**
   - TOYBOX側の`sso_callback`エンドポイントが呼び出される

2. **チケットの検証**
   - StudySphere側のSSO APIを呼び出してチケットを検証
   - ユーザー情報（`user_id`, `login_code`, `username`など）を取得

3. **アカウント存在チェック**
   - `studysphere_user_id`でTOYBOX側のユーザーを検索

4. **分岐処理**
   - **アカウントがある場合**: 自動ログインしてマイページにリダイレクト
   - **アカウントがない場合**: `/login/?ticket=xxx`にリダイレクト（チケットを保持）

5. **ログイン画面での処理**
   - チケットがある場合、`/sso/verify-and-check/` APIを呼び出し
   - アカウントがある場合: IDフィールドに自動入力、パスワードなしでログイン可能
   - アカウントがない場合: `/signup/?from=sso`にリダイレクト

6. **登録画面での処理**
   - SSO情報をセッションストレージから取得
   - IDフィールドに自動入力、パスワードフィールドは非表示
   - パスワードなしでアカウント作成可能

## 確認事項

### 1. SSO APIのエンドポイント

StudySphere側で以下のエンドポイントが利用可能か確認してください：

- **チケット生成（ログインコードから）**: `POST /api/sso/ticket/generate-by-logincode`
- **チケット検証**: `POST /api/sso/ticket/verify`

### 2. 認証トークン

StudySphere側で`SSO_SERVICE_TOKEN`が正しく設定されているか確認してください。

### 3. リダイレクトURL

TOYBOX側のコールバックURLが正しく設定されているか確認してください：

```
https://toybox.ayatori-inc.co.jp/sso/callback/
```

**重要**: 末尾のスラッシュ（`/`）を含めてください。

### 4. テスト方法

1. StudySphereにログイン
2. 「TOYBOXへ」ボタンをクリック
3. ブラウザのアドレスバーでURLを確認
   - 正しい場合: `https://toybox.ayatori-inc.co.jp/sso/callback/?ticket=xxx`
   - 間違っている場合: `https://toybox.ayatori-inc.co.jp/login/`（チケットなし）

## エラーハンドリング

### チケット生成失敗時

- エラーメッセージを表示して、StudySphere側に戻る
- または、TOYBOX側のログイン画面にリダイレクト（チケットなし）

### チケット検証失敗時

- TOYBOX側でエラーメッセージを表示
- StudySphere側に戻るオプションを提供

## セキュリティに関する注意事項

1. **HTTPSの使用**: すべての通信はHTTPSで行ってください
2. **トークンの管理**: `SSO_SERVICE_TOKEN`は機密情報として適切に管理してください
3. **チケットの有効期限**: チケットには適切な有効期限を設定してください（推奨: 5分以内）
4. **リファラー検証**: 可能であれば、リダイレクト元の検証を行ってください

## 連絡先

実装に関する質問や問題がある場合は、TOYBOX側の開発チームに連絡してください。

## 実装後の動作確認

実装後、以下の手順で動作確認を行ってください：

1. **StudySphereにログイン**
2. **「TOYBOXへ」ボタンをクリック**
3. **ブラウザのアドレスバーでURLを確認**
   - ✅ 正しい場合: `https://toybox.ayatori-inc.co.jp/sso/callback/?ticket=xxx`
   - ❌ 間違っている場合: `https://toybox.ayatori-inc.co.jp/login/`（チケットなし）

4. **TOYBOX側の動作確認**
   - アカウントがある場合: 自動ログインしてマイページにリダイレクト
   - アカウントがない場合: ログイン画面にリダイレクト（チケット付き）

## トラブルシューティング

### 問題: チケットが生成されない

**原因**: SSO APIへの接続が失敗している、または認証トークンが無効

**解決方法**:
1. `SSO_SERVICE_TOKEN`が正しく設定されているか確認
2. SSO APIのエンドポイントが正しいか確認
3. ネットワーク接続を確認

### 問題: リダイレクト先が間違っている

**原因**: コールバックURLの設定が間違っている

**解決方法**:
1. コールバックURLが `https://toybox.ayatori-inc.co.jp/sso/callback/` になっているか確認
2. 末尾のスラッシュ（`/`）を含める
3. `https://`で始まる完全なURLを使用

### 問題: チケットが無効と表示される

**原因**: チケットの有効期限が切れている、またはチケットの形式が間違っている

**解決方法**:
1. チケット生成からリダイレクトまでの時間を短縮
2. チケットの有効期限設定を確認
3. TOYBOX側のログを確認

## 参考資料（TOYBOX側の実装参考用）

必要に応じて、TOYBOX側の実装を参考にしてください：

- TOYBOX側のSSO設定ガイド（`backend/STUDYSPHERE_SSO_SETUP.md`）
- TOYBOX側のSSOサービス実装（`backend/sso_integration/services.py`）
- TOYBOX側のSSOビュー実装（`backend/sso_integration/views.py`）

**注意**: これらはTOYBOX側の実装例です。StudySphere側の環境に合わせて実装してください。

## 連絡先

実装に関する質問や問題がある場合は、TOYBOX側の開発チームに連絡してください。
