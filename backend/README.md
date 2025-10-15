# ToyBox Backend

## 概要
ToyBox アプリケーションのバックエンドAPI（Express + TypeScript + Mongoose）

## セットアップ

### 1. 依存関係のインストール
```bash
npm install
```

### 2. 環境変数の設定
`env.example` を参考に `.env` ファイルを作成してください。

```bash
cp env.example .env
```

主要な設定項目：

| 環境変数 | 説明 | デフォルト |
|---------|------|-----------|
| `MONGODB_URI` | MongoDB接続URI | `mongodb://mongo:27017/toybox` |
| `MONGODB_DB` | データベース名 | `toybox` |
| `PORT` | サーバーポート | `4000` |
| `REDIS_URL` | Redis接続URL（通知キュー用） | `redis://redis:6379` |
| `CORS_ORIGINS` | CORS許可オリジン（カンマ区切り） | `http://localhost:3000` |
| `MAX_UPLOAD_MB_AVATAR` | アバター画像上限（MB） | `2` |
| `MAX_UPLOAD_MB_HEADER` | ヘッダー画像上限（MB） | `5` |
| `MAX_UPLOAD_MB_POST` | 投稿画像上限（MB） | `10` |
| `JWT_SECRET` | JWT署名用シークレット（本番環境では必ず変更） | `change_me_strong_secret_in_production` |

### 3. 開発サーバーの起動
```bash
npm run dev
```

### 4. ビルド
```bash
npm run build
```

### 5. 本番起動
```bash
npm start
```

## API エンドポイント

### 認証
匿名認証方式を採用（`x-anon-id` ヘッダーまたはクエリパラメータ）

### 主要エンドポイント

#### 認証系
- `POST /api/auth/register` - ユーザー登録（email/password）
- `POST /api/auth/login` - ログイン
- `POST /api/auth/logout` - ログアウト
- `GET /api/auth/me` - 現在のユーザー情報取得

#### ユーザー系
- `GET /api/user/me` - 自分の情報取得（匿名認証）
- `POST /api/user/profile/bio` - 自己紹介更新
- `POST /api/user/profile/name` - 表示名更新
- `POST /api/user/profile/avatar` - アバター画像アップロード
- `POST /api/user/profile/header` - ヘッダー画像アップロード
- `POST /api/user/profile/upload?type=avatar|header` - 統合アップロード
- `PATCH /api/user/profile` - プロフィール一括更新（displayName/bio）

#### 提出系
- `POST /api/submit` - テキストベース提出＆抽選
- `POST /api/submit/upload` - 画像アップロード付き提出
- `GET /api/submissions/me` - 自分の提出一覧

#### フィード系
- `GET /api/feed` - 全体フィード（ページング対応）
- `GET /api/user/profile/:anonId` - 公開プロフィール
- `GET /api/user/submissions/:anonId` - ユーザー別提出一覧

#### お題系
- `GET /api/topic/work` - 業務系お題
- `GET /api/topic/play` - お遊び系お題

#### 監視系
- `GET /health` - ヘルスチェック
- `GET /ready` - レディネス
- `GET /metrics` - Prometheusメトリクス

## 開発

### テスト
```bash
npm test
```

### ディレクトリ構成
```
src/
  ├── api/           # ルーター（機能別）
  ├── dto/           # レスポンス型定義
  ├── lib/           # 共通ライブラリ（アップロード等）
  ├── middleware/    # ミドルウェア（認証、エラーハンドリング等）
  ├── queue/         # キュー（通知）
  ├── services/      # ビジネスロジック
  ├── utils/         # ユーティリティ（ログ、メトリクス、時刻等）
  ├── validation/    # バリデーションスキーマ（zod）
  ├── workers/       # バックグラウンドワーカー
  └── server.ts      # エントリーポイント
models/              # Mongooseモデル定義
```

## トラブルシューティング

### アップロードエラー
- `413 Payload Too Large`: ファイルサイズが上限を超えています。環境変数 `MAX_UPLOAD_MB_*` を確認してください
- `400 Invalid file type`: 許可されていないファイル形式です（jpg, jpeg, png, webp のみ許可）

### CORS エラー
- `CORS_ORIGINS` 環境変数にフロントエンドのオリジンが含まれているか確認してください
- カンマ区切りで複数指定可能（例: `http://localhost:3000,https://example.com`）

### 日付/時刻
- 1日の境界判定は **日本時間（JST: UTC+9）** を基準としています
- データベースにはUTCで保存されますが、集計・制限判定はJST基準で動作します

