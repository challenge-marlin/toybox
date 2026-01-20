# Caddyfileのuploads設定修正

## 問題
Caddyfileの`/uploads/*`の設定で、`root * /app/public/uploads`としているが、これだと`/uploads/submissions/10_1766547801.png`にアクセスしたときに`/app/public/uploads/uploads/submissions/10_1766547801.png`を探してしまう可能性がある。

## 解決方法

Caddyfileの`handle /uploads/*`の設定を修正する必要があります。

### 修正前
```caddy
handle /uploads/* {
    root * /app/public/uploads
    file_server
}
```

### 修正後（オプション1: rootを削除）
```caddy
handle /uploads/* {
    file_server root /app/public/uploads
}
```

### 修正後（オプション2: rewriteを使用）
```caddy
handle /uploads/* {
    rewrite * /uploads{path}
    file_server root /app/public/uploads
}
```

### 修正後（オプション3: strip_prefixを使用）
```caddy
handle /uploads/* {
    file_server root /app/public/uploads strip_prefix /uploads
}
```

最もシンプルなのは、`root`ディレクティブを削除して、`file_server`に直接`root`を指定する方法です。
