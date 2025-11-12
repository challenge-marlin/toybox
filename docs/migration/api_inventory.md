### ToyBox API インベントリ（現行: Express + MongoDB）

最終更新: 自動抽出に基づく要約。基準パスは `/api`。一部、フロントの Next.js サーバールートも末尾に記載。


## 認証・認可
- 認証方式: JWT（HttpOnly Cookie `token` または `Authorization: Bearer <jwt>`）。
- `optionalAuth`: トークンがあれば `req.userId`/`req.userEmail` を付与（未認証でも通過）。
- `requireAnonAuth`: `userId` から `User.anonId` を引き当て、`req.anonId` を必須化（未認証は 401）。
- 匿名IDの直接ヘッダ指定（`x-anon-id`）は廃止方向。内部的にはレート制限キーの後方互換として参照。

## レート制限
- スコープ: `/api` 配下の書き込み系（GET/OPTIONS/HEAD を除く）。
- ルール: 1分あたり最大 120 リクエスト（キーは `anon:<anonId>` 優先、なければ `ip:<addr>`）。
- レスポンスヘッダ: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`。超過時は 429 と `Retry-After`。

## ログ/メトリクス/エラー方針
- リクエストログ: `request.start`（受信時）/`request.end`（終了時; status, ms）。JSON 1行構造化ログ。
- 監視メトリクス: `/metrics`（Prometheus 互換のプレーンテキスト）。リクエスト総数、500件数、フィード配信数、プロフィール閲覧数、429/401回数、いいね増減、WebVitals平均、FE計測等。
- エラーハンドリング: 例外を集中処理（`centralErrorHandler`）。代表ケース:
  - Zod バリデーション: 400 `VALIDATION_ERROR`（issues）
  - アップロード: 413 `PAYLOAD_TOO_LARGE`、400 `INVALID_FILE_TYPE`
  - アプリ例外: `AppError`（status/code/message）
  - Mongoose Validation/Cast: 400 に正規化
  - 上記以外: 500 `INTERNAL_SERVER_ERROR`


## エンドポイント一覧

### ヘルス/監視（認証不要）
- GET `/health`
  - 200: `{ "status": "ok" }`
- GET `/ready`
  - 200/503: `{ "ready": true|false }`
- GET `/metrics`
  - 200: Prometheus テキスト


### 認証系（公開）
- POST `/api/auth/register`
  - body: `{ "username": string(3-30,英数_), "password": string(8-128), "displayName": string(1-50) }`
  - 201: `{ "ok": true, "user": { id, email, username, displayName, anonId } }`（Cookie に `token` 設定）
- POST `/api/auth/login`
  - body: `{ "email"?: string | "username"?: string, "password": string }`（email/username のいずれか必須）
  - 200: `{ "ok": true, "user": { id, email, username, displayName, anonId } }`（Cookie に `token` 設定）
- POST `/api/auth/logout`
  - 200: `{ "ok": true, "message": "Logged out successfully" }`（Cookie クリア）
- GET `/api/auth/me`
  - 200: `{ "ok": true|false, "user": null | { id, email, displayName, anonId } }`
- GET `/api/auth/discord/login`
  - 302: Discord OAuth2 認可URLへリダイレクト（環境変数必須）
- GET `/api/auth/discord/callback?code=...`
  - 302: `/mypage` へ。内部でユーザー作成/更新し `token` 設定。
- POST `/api/auth/deleteAccount`（要認証）
  - 200: `{ "ok": true }`（関連 `Submission` 全削除、`UserMeta`/`User` 削除、Cookie クリア）


### マイページ/一般公開（`optionalAuth` 全体適用。必要箇所のみ都度 `requireAnonAuth`）
- POST `/api/contact`
  - body: `{ "name": string, "email"?: string, "message": string(>=5) }`
  - 200: `{ "ok": true }`（環境で SMTP 未設定時は jsonTransport）
- GET `/api/topic/work` / GET `/api/topic/play`
  - 200: `{ "topic": string }`（日替わり）
- GET `/api/topic/fetch?type=work|play`
  - 200: `{ "topic": string }`（外部サイトから抽出）、502/500 エラーあり
- GET `/api/feed?limit=1..50&cursor=<ISO>`
  - 200: `{ "items": [{ id, anonId, displayName?, createdAt, imageUrl?, videoUrl?, avatarUrl?, displayImageUrl?, title?, gameUrl?, likesCount, liked }], "nextCursor": ISO|null }`
- GET `/api/submissions/me?limit=1..50`（要 `requireAnonAuth`）
  - 200: `{ "items": [{ id, createdAt, imageUrl?, videoUrl?, displayImageUrl?, gameUrl?, likesCount, liked }] }`
- GET `/api/notifications?limit=..&offset=..`（要 `requireAnonAuth`）
  - 200: `{ "items": Notification[], "unread": number, "nextOffset": number|null }`
- POST `/api/notifications/read`（要 `requireAnonAuth`）
  - body: `{ "indexes"?: number[] }`（未指定時は一括既読）
  - 200: `{ "ok": true|false }`
- GET `/api/user/profile/:anonId`
  - 200: `UserProfileDto`（displayName, avatarUrl, headerUrl, bio, activeTitle 等）
- GET `/api/user/submissions/:anonId?limit=..&cursor=<ISO>`
  - 200: `{ "items": [...], "nextCursor": ISO|null }`
- GET `/api/submissions/:id`
  - 200: 詳細＋前後ID `{ id, anonId, displayName?, avatarUrl?, createdAt, imageUrl?, videoUrl?, gameUrl?, displayImageUrl?, likesCount, liked, prevId, nextId }`
- DELETE `/api/submissions/:id`（要 `requireAnonAuth`）
  - 200: `{ "ok": true }`（所有者のみ。現状はハードデリート）
- POST `/api/submissions/:id/like`（要 `requireAnonAuth`）
  - 200: `{ "ok": true, "likesCount": number, "liked": true }`
- DELETE `/api/submissions/:id/like`（要 `requireAnonAuth`）
  - 200: `{ "ok": true, "likesCount": number, "liked": false }`


### ユーザー（要 `requireAnonAuth`）
- GET `/api/user/me`
  - 200: `UserMeDto`（anonId, activeTitle, cardsAlbum, lotteryBonusCount 等）
- POST `/api/user/nextTitle`
  - 200: `{ ok: true, title: string, until: ISO|null }`（称号即時付与＋カード付与）
- POST `/api/user/profile/bio`
  - body: `{ "bio": string(<=1000) }`
  - 200: `{ ok: true, bio }`
- POST `/api/user/profile/name`
  - body: `{ "displayName": string(1..50) }`
  - 200: `{ ok: true, displayName }`
- POST `/api/user/profile/avatar`（multipart/form-data, `file`）
  - 200: `{ ok: true, avatarUrl }`
- POST `/api/user/profile/header`（multipart/form-data, `file`）
  - 200: `{ ok: true, headerUrl }`
- POST `/api/user/profile/upload?type=avatar|header`（multipart/form-data, `file`）
  - 200: `{ ok: true, avatarUrl|headerUrl }`
- PATCH `/api/user/profile`
  - body: 任意組合せ `{ displayName?, bio?, avatarUrl?, headerUrl? }`
  - 200: `UserMeDto`


### 提出（要 `requireAnonAuth`）
- POST `/api/submit`
  - body: `{ aim: string(<=100), steps: string[3], frameType: string, imageUrl?, videoUrl?, gameUrl? }`
  - 200: `SubmissionResultDto`（`jpResult` は現状 `'none'`、即時報酬の称号/カードを返す）
- POST `/api/submit/upload`（画像/動画アップロードのみ先行。multipart/form-data, `file`）
  - 200: 画像 `{ ok: true, imageUrl, displayImageUrl? }` / 動画 `{ ok: true, videoUrl }`


### カード（要 `requireAnonAuth`）
- POST `/api/cards/generate`
  - body: `{ "type": "Character"|"Effect" }`（省略時 Character）
  - 200: `{ ok: true, card, obtainedAt }`（カードアルバムに追加）
- GET `/api/cards/me`
  - 200: `{ ok: true, entries: [{ id, obtainedAt, meta: cardMeta|null }, ...] }`
- GET `/api/cards/summary`
  - 200: `{ ok: true, total, rarity: { SSR, SR, R, N }, byAttr }`


## Next.js サーバールート（フロントエンド）

> 旧構成では「server actions 相当」も対象のため記載。

- POST `/api/share/discord`（Next.js `app/api/share/discord/route.ts`）
  - body: `{ "assetId": string }`
  - 動作: バックエンドからアセット解決 → Discord Bot API へメディア投稿（20MB制限/レート制御あり）
  - 200: `{ ok: true, discordMessageId }` / 4xx/5xx: `{ ok: false, error }`


## サンプルレスポンス（最小）

```json
// POST /api/submit
{
  "jpResult": "none",
  "probability": 0,
  "bonusCount": 3,
  "rewardTitle": "工房の匠",
  "rewardCardId": "C012",
  "rewardCard": { "card_id": "C012", "card_name": "Brass Knight", "rarity": "SR", "image_url": "/uploads/cards/C012.webp" },
  "jackpotRecordedAt": null
}
```


