# メール送信問題の診断結果

## 問題の原因

**SMTP認証情報が設定されていません**

## 現在の状況

### ✅ 設定されている項目
- `EMAIL_HOST=mail1006.conoha.ne.jp`
- `EMAIL_PORT=587`
- `EMAIL_USE_TLS=true`
- `DEFAULT_FROM_EMAIL=noreply@ayatori-inc.co.jp`

### ❌ 設定されていない項目（必須）
- `EMAIL_HOST_USER=` （空）
- `EMAIL_HOST_PASSWORD=` （空）
- `CONTACT_EMAIL=` （`.env`に存在しない）

## エラーメッセージ

```
SMTPRecipientsRefused: {'maki@ayatori-inc.co.jp': (454, b'4.7.1 <maki@ayatori-inc.co.jp>: Relay access denied')}
```

このエラーは、SMTPサーバーが認証を要求しているが、認証情報が提供されていないことを示しています。

## 解決方法

`.env`ファイルに以下の設定を追加してください：

```env
EMAIL_HOST_USER=your-email@ayatori-inc.co.jp
EMAIL_HOST_PASSWORD=your-password
CONTACT_EMAIL=maki@ayatori-inc.co.jp
```

または、`SMTP_*`形式を使用する場合：

```env
SMTP_USER=your-email@ayatori-inc.co.jp
SMTP_PASS=your-password
CONTACT_EMAIL=maki@ayatori-inc.co.jp
```

## 設定後の確認手順

1. `.env`ファイルを編集して認証情報を追加
2. Dockerコンテナを再起動：
   ```powershell
   docker compose restart web
   ```
3. メール送信をテスト：
   ```powershell
   docker compose exec web python /app/test_email.py
   ```

## 補足情報

- ConoHaのメールサーバー（`mail1006.conoha.ne.jp`）は認証が必須です
- 認証情報はConoHaのコントロールパネルで確認できます
- 送信元メールアドレス（`DEFAULT_FROM_EMAIL`）は、ConoHaのドメイン（`ayatori-inc.co.jp`）である必要があります

