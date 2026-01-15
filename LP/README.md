# TOYBOX LP（ランディングページ）

## 概要

TOYBOXのランディングページです。HTML、CSS、JavaScriptのみで構成されており、PHPやサーバーサイドの処理は不要です。

## ファイル構成

- `index.html` - メインページ
- `privacy.html` - プライバシーポリシーページ
- `assets/` - CSS、JavaScript、画像ファイル
  - `css/style.css` - スタイルシート
  - `js/script.js` - JavaScript
  - `images/` - 画像ファイル
    - `ogp.png` - OGP画像（1200x630px推奨）※作成が必要
  - `videos/` - 動画ファイル

## OGP画像について

OGP画像は以下の場所に配置してください：

```
LP/assets/images/ogp.png
```

### OGP画像の推奨仕様
- **サイズ**: 1200px × 630px
- **形式**: PNG または JPG
- **ファイル名**: `ogp.png` または `og-image.png`

### 設定方法

1. OGP画像を`assets/images/`フォルダに配置
2. `index.html`のOGPタグ内の`og:image`と`twitter:image`のURLを実際のドメインに変更
   ```html
   <meta property="og:image" content="https://yourdomain.com/assets/images/ogp.png">
   <meta name="twitter:image" content="https://yourdomain.com/assets/images/ogp.png">
   ```

## 起動方法

### ローカルで確認する場合

1. 任意のWebサーバーで`index.html`を開く
2. または、ブラウザで直接`index.html`を開く

### 簡単なHTTPサーバーを使用する場合（Python）

```powershell
cd LP
python -m http.server 8080
```

ブラウザで http://localhost:8080/ にアクセス

### Node.jsを使用する場合

```powershell
cd LP
npx http-server -p 8080
```

ブラウザで http://localhost:8080/ にアクセス

## お問い合わせ

お問い合わせは、[AYATORI.Incのお問い合わせフォーム](https://www.ayatori-inc.co.jp/?page_id=7)からお願いいたします。

## 注意事項

- PHPやサーバーサイドの処理は不要です
- すべてのリンクは外部リンク（AYATORI.Incのお問い合わせフォーム）に設定されています
- 静的ファイルのみで動作します
- OGP画像のURLは本番環境のドメインに変更してください
