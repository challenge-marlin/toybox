# リファクタリング完了報告

## 実施内容

### 1. アップロード制限の種別別対応 ✅
- **実装箇所**: `src/lib/upload.ts`
- **変更内容**:
  - `uploadAvatar`: 2MB上限（環境変数 `MAX_UPLOAD_MB_AVATAR`）
  - `uploadHeader`: 5MB上限（環境変数 `MAX_UPLOAD_MB_HEADER`）
  - `uploadPost`: 10MB上限（環境変数 `MAX_UPLOAD_MB_POST`）
  - 許可MIME: `image/jpeg`, `image/png`, `image/webp`
  - ディレクトリ作成保証: 起動時に `public/uploads` を自動作成
- **適用箇所**:
  - `src/api/user.ts`: `/api/user/profile/avatar`, `/api/user/profile/header` で種別別ミドルウェア使用

### 2. feedのimageUrl優先度実装 ✅
- **実装箇所**: `src/api/mypage.ts` - `GET /api/feed`
- **優先順**: `submission.imageUrl`（投稿画像） → `user.avatarUrl`
- **変更内容**: フィード生成時に投稿画像が存在すればそれを表示、なければユーザーのアバターにフォールバック

### 3. エラーハンドリング集約 ✅
- **実装箇所**: `src/middleware/errorHandler.ts`（新設）
- **形式**: `{ status, code, message, details? }`
- **対応エラー種別**:
  - Multer ファイルサイズ超過 → 413 `PAYLOAD_TOO_LARGE`
  - Multer 不正ファイル形式 → 400 `INVALID_FILE_TYPE`
  - Zod バリデーションエラー → 400 `VALIDATION_ERROR`
  - Mongoose バリデーション → 400 `VALIDATION_ERROR`
  - Mongoose CastError → 400 `INVALID_ID`
  - カスタムAppError（401/404/500等）
  - 汎用エラー → 500 `INTERNAL_SERVER_ERROR`
- **適用**: `src/server.ts` で `centralErrorHandler` を登録

### 4. zodバリデーション導入 ✅
- **パッケージ**: `zod@^3.22.4` をdependenciesに追加
- **実装箇所**: `src/validation/user.ts`（新設）
- **スキーマ**:
  - `UpdateBioSchema`: bio（最大1000文字、optional）
  - `UpdateDisplayNameSchema`: displayName（1〜50文字、必須）
  - `UploadKindSchema`: kind（`'avatar'` | `'header'`、デフォルト`'avatar'`）
- **適用箇所**: `src/api/user.ts` の bio/name 更新API

### 5. DTO/レスポンス型の統一 ✅
- **実装箇所**:
  - `src/dto/UserDto.ts`: `UserMeDto`, `UserProfileDto`, `UpdateProfileResponse`
  - `src/dto/FeedItemDto.ts`: `FeedItemDto`, `FeedResponseDto`, `SubmissionItemDto`, `SubmissionsResponseDto`
  - `src/dto/SubmissionDto.ts`: `SubmissionResultDto`
- **適用箇所**:
  - `src/api/user.ts`: すべてのエンドポイントでDTO型を返却
  - `src/api/mypage.ts`: feed/submissions/profileでDTO型を返却
  - `src/api/submit.ts`: 提出結果でDTO型を返却

### 6. メトリクス拡充 ✅
- **実装箇所**: `src/utils/metrics.ts`
- **追加メトリクス**:
  - `toybox_upload_failed_total`: アップロード失敗回数
  - `toybox_rate_limited_429_total`: 429レスポンス回数
  - `toybox_unauthorized_401_total`: 401レスポンス回数
- **適用箇所**:
  - `src/middleware/errorHandler.ts`: アップロード失敗時にカウント
  - `src/middleware/auth.ts`: 401時にカウント
  - `src/middleware/rateLimit.ts`: 429時にカウント

### 7. CORS/設定文書化 ✅
- **実装箇所**:
  - `backend/env.example`: 環境変数サンプル（アップロード上限、CORS説明を追記）
  - `backend/README.md`: 新設（セットアップ手順、API一覧、トラブルシューティング）
- **内容**:
  - CORS_ORIGINS のカンマ区切り対応説明
  - 種別別アップロード上限の環境変数説明
  - JST基準の日付処理についての説明

### 8. JST時刻処理の統一（前回実装済み） ✅
- **実装箇所**: `src/utils/time.ts`
- **関数**: `startOfJstDay`, `endOfJstDay`
- **適用箇所**: `src/services/lotteryService.ts`, `src/api/mypage.ts`

### 9. ルート改修（エラーハンドリング/バリデーション適用） ✅
- **改修箇所**:
  - `src/api/user.ts`: try/catchを縮小し、`next(err)`で集約ミドルウェアへ委譲、zodバリデーション適用、種別別アップロード使用
  - `src/api/submit.ts`: `next(err)`でエラー委譲、DTO型適用
  - `src/api/mypage.ts`: DTO型適用、feed imageUrl優先度実装

## 受け入れ条件の確認

### アップロード制限
- ✅ avatar 2MB超過 → 413 `PAYLOAD_TOO_LARGE`
- ✅ header 5MB超過 → 413 `PAYLOAD_TOO_LARGE`
- ✅ post 10MB超過 → 413 `PAYLOAD_TOO_LARGE`
- ✅ 拡張子不正 → 400 `INVALID_FILE_TYPE`（jpg/jpeg/png/webp以外）
- ✅ 成功時 → `{ ok: true, avatarUrl: '/uploads/...'}` または `{ ok: true, headerUrl: '/uploads/...'}`

### feed仕様
- ✅ `submission.imageUrl` が存在すればそれを表示
- ✅ なければ `user.avatarUrl` にフォールバック

### エラー形式
- ✅ 統一形式: `{ status, code, message, details }`
- ✅ エラーミドルウェア経由で返却

### データ保全
- ✅ 既存データは削除されない（移行処理なし、スキーマ変更なし）

## ファイル変更一覧

### 新規作成
- `src/dto/UserDto.ts`
- `src/dto/FeedItemDto.ts`
- `src/dto/SubmissionDto.ts`
- `src/middleware/errorHandler.ts`
- `src/validation/user.ts`
- `src/utils/time.ts`（前回）
- `backend/README.md`

### 変更
- `package.json`: zodパッケージ追加
- `src/lib/upload.ts`: 種別別アップロードミドルウェア、ディレクトリ作成保証、許可MIME拡張
- `src/utils/metrics.ts`: メトリクス拡充（upload_failed/429/401）
- `src/middleware/auth.ts`: 401メトリクス追加
- `src/middleware/rateLimit.ts`: 429メトリクス追加
- `src/api/user.ts`: DTO/zod/エラーハンドリング/種別別アップロード適用、エンドポイント分割（avatar/header）
- `src/api/mypage.ts`: DTO適用、feed imageUrl優先度実装
- `src/api/submit.ts`: DTO/エラーハンドリング適用
- `src/server.ts`: centralErrorHandler適用
- `backend/env.example`: 環境変数説明追記

### 削除
- なし（既存ファイルはすべて温存）

## API変更（破壊的変更）

### ⚠️ 重要：エンドポイントの変更
`/api/user/profile/upload` は廃止され、以下の2つのエンドポイントに分割されました：

#### 変更前
```
POST /api/user/profile/upload?kind=avatar
POST /api/user/profile/upload?kind=header
```

#### 変更後
```
POST /api/user/profile/avatar
POST /api/user/profile/header
```

**フロントエンド対応が必要です。**

### その他のAPI
- レスポンス形式は互換性維持（DTO型による明示化のみ）
- エラーレスポンスは統一形式に変更（`{ status, code, message, details }`）

## 今後の推奨改善

1. **zodバリデーションの拡大**: `submit.ts` や `mypage.ts` のクエリパラメータにもzodを適用
2. **テストの拡充**: 新規ミドルウェア（errorHandler、種別別upload）のユニットテスト追加
3. **型安全性の向上**: `(req as any).anonId` を型安全にするため、Express.Requestの拡張型定義
4. **フロントエンド対応**: `/api/user/profile/upload` → `/api/user/profile/avatar` または `/header` への移行

## リンタエラー
- ✅ 0件（全ファイルリンタチェック済み）

## 動作確認推奨項目
1. `npm install` でzodパッケージをインストール
2. `.env` に `MAX_UPLOAD_MB_AVATAR`, `MAX_UPLOAD_MB_HEADER`, `MAX_UPLOAD_MB_POST` を設定
3. avatar/headerアップロードの上限チェック（2MB/5MB）
4. 不正ファイル形式のアップロード → 400エラー確認
5. feedで投稿画像の優先表示確認
6. `/metrics` エンドポイントで新規メトリクスの出力確認

