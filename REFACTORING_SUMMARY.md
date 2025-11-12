# リポジトリリファクタリング完了報告

## 実施内容

### 1. レガシーコードの整理 ✅

Django移行前のコードを`doc/legacy/`ディレクトリに移動しました：

- **`doc/legacy/backend/`** - Express + TypeScript + MongoDB のバックエンドコード
  - `src/` - TypeScriptソースコード
  - `dist/` - コンパイル済みJavaScript
  - `models/` - TypeScriptモデル定義
  - `package.json`, `package-lock.json`, `tsconfig.json` - Node.js設定ファイル
  - `README.md` - レガシーバックエンドのREADME

- **`doc/legacy/frontend/`** - Next.js のフロントエンドコード
  - Next.jsアプリケーション全体

### 2. ドキュメントの整理 ✅

ルートディレクトリのドキュメントファイルを`doc/`サブディレクトリに整理：

- **`doc/deployment/`** - デプロイメント関連
  - `DEPLOYMENT_GUIDE.md`
  - `DEPLOYMENT_SUMMARY.md`
  - `DEPLOYMENT.md`

- **`doc/setup/`** - セットアップ関連
  - `SETUP_INSTRUCTIONS.md`
  - `SETUP_DEPLOYMENT.md`
  - `SETUP_APP_USER.md`
  - セットアップスクリプト（`.sh`ファイル）

- **`doc/troubleshooting/`** - トラブルシューティング
  - `TROUBLESHOOTING_NGINX.md`
  - `BUGFIX_SUMMARY.md`
  - `FRONTEND_FIXES_GUIDE.md`

- **`doc/`** - その他のドキュメント
  - `ACCESS_VIA_VNC.md`
  - `SSH_CONNECTION_GUIDE.md`
  - `ホスティング.md`
  - その他

### 3. レガシーファイルの移動 ✅

- バッチファイル（`.bat`）→ `doc/legacy/`
- レガシーのDocker設定ファイル → `doc/legacy/`
- レガシーのREADMEファイル → `doc/legacy/backend/`

### 4. 設定ファイルの更新 ✅

- **`.gitignore`** - Django関連の除外パターンを追加
- **`README.md`** - 新しいリポジトリ構造を反映

## 新しいリポジトリ構造

```
toybox/
├── backend/              # Django バックエンド（現在の実装）
│   ├── users/
│   ├── submissions/
│   ├── lottery/
│   ├── gamification/
│   ├── sharing/
│   ├── adminpanel/
│   ├── frontend/         # Djangoテンプレート
│   └── ...
├── docs/                 # 移行ドキュメント
│   └── migration/
├── doc/                  # その他のドキュメント
│   ├── legacy/          # Django移行前のコード
│   │   ├── backend/     # Express + TypeScript
│   │   └── frontend/    # Next.js
│   ├── deployment/      # デプロイメント関連
│   ├── setup/           # セットアップ関連
│   └── troubleshooting/ # トラブルシューティング
├── scripts/              # ユーティリティスクリプト
└── README.md            # プロジェクト概要
```

## 注意事項

- **`backend/public/uploads/cards/`** - カード画像はDjangoで使用中のため、そのまま保持
- **レガシーコード** - 参考用として保存されていますが、現在の実装では使用されていません

## 次のステップ

1. レガシーコードの参照が必要な場合は`doc/legacy/`を確認
2. 現在のDjango実装については`backend/README_DJANGO.md`を参照
3. 移行ドキュメントについては`docs/migration/`を参照

