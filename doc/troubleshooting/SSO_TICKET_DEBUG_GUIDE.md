# SSOチケットデバッグガイド

## 概要

ブラウザのコンソールに`[SSO] checkSSOTicket called, ticket:`と表示されている場合、チケットの内容を確認する方法を説明します。

## 確認方法

### 方法1: ブラウザのコンソールで確認

1. **ブラウザの開発者ツールを開く**
   - Chrome/Edge: `F12` または `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
   - Firefox: `F12` または `Ctrl+Shift+K` (Windows) / `Cmd+Option+K` (Mac)

2. **コンソールタブを開く**
   - 開発者ツールの「Console」タブをクリック

3. **ログを確認**
   - `[SSO]`で始まるログを探す
   - 以下の情報が表示されます：
     ```
     [SSO] ========== SSO Debug Info ==========
     [SSO] Current URL: https://example.com/login/?ticket=xxx
     [SSO] URL Search: ?ticket=xxx
     [SSO] All URL Parameters: {ticket: "xxx"}
     [SSO] Ticket value: xxx
     [SSO] Ticket type: string
     [SSO] Ticket length: 32
     [SSO] Ticket preview (first 20 chars): abc123def456ghi789...
     [SSO] ====================================
     ```

### 方法2: URLパラメータを直接確認

ブラウザのアドレスバーでURLを確認：

```
https://yourdomain.com/login/?ticket=チケットの値
```

**例**:
```
https://toybox.example.com/login/?ticket=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

### 方法3: ブラウザのコンソールで手動実行

コンソールで以下のコマンドを実行：

```javascript
// URLパラメータを取得
const urlParams = new URLSearchParams(window.location.search);
const ticket = urlParams.get('ticket');

// チケットの情報を表示
console.log('Ticket:', ticket);
console.log('Ticket exists:', !!ticket);
console.log('Ticket length:', ticket ? ticket.length : 0);
console.log('Full URL:', window.location.href);
console.log('All params:', Object.fromEntries(urlParams));
```

### 方法4: ネットワークタブでAPIリクエストを確認

1. **開発者ツールの「Network」タブを開く**
2. **ページをリロード**（`F5`）
3. **`/sso/verify-and-check/`のリクエストを探す**
4. **リクエストの詳細を確認**:
   - 「Payload」タブで送信されたチケットを確認
   - 「Response」タブでサーバーからの応答を確認

### 方法5: サーバー側のログを確認

SSH接続またはWinSCPのターミナル機能で：

```bash
# Dockerコンテナのログを確認
cd /var/www/toybox/backend
docker compose logs web --tail=100 | grep -i sso

# または、リアルタイムでログを監視
docker compose logs web -f | grep -i sso
```

## よくある問題と解決方法

### 問題1: チケットが`null`または`undefined`

**症状**: コンソールに`ticket: null`または`ticket: undefined`と表示される

**原因**:
- URLに`ticket`パラメータが含まれていない
- StudySphereからのリダイレクトが正しく行われていない

**解決方法**:
1. StudySphere側で「TOYBOXへ」ボタンをクリックした際のURLを確認
2. URLに`?ticket=xxx`が含まれているか確認
3. StudySphere側の設定を確認（コールバックURLが正しいか）

### 問題2: チケットが空文字列

**症状**: コンソールに`ticket: ""`と表示される

**原因**:
- URLに`?ticket=`とパラメータ名だけが含まれている
- StudySphere側でチケットが正しく生成されていない

**解決方法**:
1. StudySphere側の管理者に連絡して、チケット生成を確認
2. `SSO_SERVICE_TOKEN`が正しく設定されているか確認

### 問題3: チケットが表示されない

**症状**: コンソールに`ticket:`と表示されるが値が表示されない

**原因**:
- チケットが非常に長い文字列で、コンソールで省略されている可能性

**解決方法**:
```javascript
// コンソールで実行
const urlParams = new URLSearchParams(window.location.search);
const ticket = urlParams.get('ticket');
console.log('Full ticket:', JSON.stringify(ticket));
```

## デバッグ用コードの追加

より詳細なデバッグ情報が必要な場合は、`login.html`に以下のコードが既に追加されています：

```javascript
console.log('[SSO] ========== SSO Debug Info ==========');
console.log('[SSO] Current URL:', window.location.href);
console.log('[SSO] URL Search:', window.location.search);
console.log('[SSO] All URL Parameters:', Object.fromEntries(urlParams));
console.log('[SSO] Ticket value:', ticket);
console.log('[SSO] Ticket type:', typeof ticket);
console.log('[SSO] Ticket length:', ticket ? ticket.length : 0);
if (ticket) {
    console.log('[SSO] Ticket preview (first 20 chars):', ticket.substring(0, 20) + '...');
}
console.log('[SSO] ====================================');
```

## 次のステップ

チケットが正しく取得できている場合：
1. APIリクエストが正しく送信されているか確認（Networkタブ）
2. サーバー側のログでエラーがないか確認
3. `STUDYSPHERE_SSO_SETUP.md`で設定を確認

チケットが取得できていない場合：
1. StudySphere側の設定を確認
2. リダイレクトURLが正しいか確認
3. StudySphere側の管理者に連絡

## 関連ドキュメント

- `STUDYSPHERE_SSO_SETUP.md` - StudySphere SSO設定ガイド
- `STUDYSPHERE_SSO_UPDATE_UPLOAD_LIST.md` - 更新ファイルリスト
