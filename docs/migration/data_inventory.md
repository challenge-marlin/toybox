### データインベントリ（現行: MongoDB / Mongoose）

抽出対象のコレクションと推定スキーマ、主要インデックス、参照関係を整理。


## コレクション一覧

### 1) `users`（`models/User.ts`）
- 概要: ログイン用ユーザー。`anonId` で `user_meta` と接続。
- フィールド
  - `email?: string`（任意, 小文字正規化, trim, unique 部分インデックス）
  - `password: string`（必須, bcrypt ハッシュ）
  - `displayName?: string`（任意, max 50）
  - `anonId: string`（必須, index）
  - `username?: string`（任意, 3..30, 英数_, 小文字化, trim, unique 部分インデックス）
  - `createdAt: Date`（デフォルト自動, timestamps）
  - `updatedAt: Date`（デフォルト自動, timestamps）
- 主要インデックス
  - `{ email: 1 }` unique, `partialFilterExpression: { email: { $exists: true, $type: 'string' } }`
  - `{ username: 1 }` unique, `partialFilterExpression: { username: { $exists: true, $type: 'string' } }`
  - `{ anonId: 1 }`
- 参照関係
  - `anonId` → `user_meta.anonId`（1:1 相当）
  - `anonId` → `submissions.submitterAnonId`（1:多）


### 2) `user_meta`（`models/UserMeta.ts`）
- 概要: 表示名/プロフィール/称号/カード、通知、いいね等のユーザー付帯情報。
- フィールド
  - `anonId: string`（必須, unique, index）
  - `lotteryBonusCount: number`（必須, min 0, default 0）
  - `cardsAlbum: { id: string; obtainedAt?: Date }[]`（default []）
  - `activeTitle?: string`（任意, 現在の称号）
  - `activeTitleUntil?: Date`（任意, 称号の有効期限）
  - `displayName?: string`（任意）
  - `bio?: string`（任意, ~1000）
  - `avatarUrl?: string`（任意, `/uploads/...` or http/https）
  - `headerUrl?: string`（任意, 同上）
  - `likedSubmissionIds?: string[]`（任意, default []）
  - `notifications?: { type:'like', fromAnonId:string, submissionId:string, message:string, createdAt:Date, read?:boolean }[]`（任意, default []）
  - `createdAt: Date`（timestamps）
  - `updatedAt: Date`（timestamps）
- 主要インデックス
  - `{ anonId: 1 }` unique
- 参照関係
  - `anonId` ← `users.anonId`（1:1）
  - `cardsAlbum[].id` はマスタデータ（`data/cardMaster.ts`でロード）に対応（DB外部）。
  - `likedSubmissionIds[]` は `submissions._id` を文字列で保持（DB参照は手動）。


### 3) `submissions`（`models/Submission.ts`）
- 概要: 投稿（テキスト/画像/動画/ゲームURL）。いいね数を集計保持。
- フィールド
  - `submitterAnonId: string`（必須, index）
  - `aim: string`（必須, max 100）
  - `steps: string[3]`（必須, 厳密に3要素）
  - `jpResult: 'win'|'lose'|'none'`（必須, default 'none'）
  - `frameType: string`（必須）
  - `imageUrl?: string`（任意, `/uploads/...`）
  - `videoUrl?: string`（任意, `/uploads/...`）
  - `gameUrl?: string`（任意, `/uploads/...` 展開先の index.html）
  - `likesCount?: number`（任意, default 0, min 0）
  - `createdAt: Date`（timestamps+default now）
  - `updatedAt: Date`（timestamps+default now, save 前に更新）
- 主要インデックス
  - `{ submitterAnonId: 1 }`
  - 推奨（将来）: `{ createdAt: -1 }`（フィード/ページングパターン最適化）
- 参照関係
  - `submitterAnonId` ← `user_meta.anonId`（1:多）


### 4) `jackpotwins`（`models/JackpotWin.ts`）
- 概要: ジャックポットの当選記録（現在は抽選機能廃止のため未使用/レガシー）。
- フィールド
  - `anonId: string`（必須, index）
  - `displayName?: string`（任意）
  - `createdAt: Date`（必須, default now, `updatedAt` 無効）
- 主要インデックス
  - `{ anonId: 1 }`
- 参照関係
  - なし（表示用途の履歴想定）


## ストレージ/外部データ
- ファイルアップロード: `public/uploads/**` を静的配信（`/uploads/...`）。キャッシュ 1h。
  - 種別: アバター/ヘッダー/投稿画像・動画/展開済みゲーム（zip 解凍後 `index.html` 検索）
  - サイズ/拡張子制限: アップローダの設定に依存（Multer, `MAX_UPLOAD_MB_*`）
- カードマスタ: `backend/src/data/cardMaster.ts`（TSV 由来）。DB非保持、アプリ起動時ロード。


## 参照関係図（概念）
- `users.anonId` 1 — 1 `user_meta.anonId`
- `user_meta.anonId` 1 — * `submissions.submitterAnonId`
- `user_meta.likedSubmissionIds[]` → `submissions._id`（非外部キー, 文字列保持）


## 型/必須/デフォルトの要約（抜粋）
- 必須: `users.password`, `users.anonId`, `user_meta.anonId`, `user_meta.lotteryBonusCount`, `submissions.submitterAnonId`, `submissions.aim`, `submissions.steps(3)`, `submissions.jpResult`, `submissions.frameType`
- 任意: `users.email`, `users.displayName`, `users.username`, `user_meta.displayName`, `bio`, `avatarUrl`, `headerUrl`, `cardsAlbum`, `likedSubmissionIds`, `notifications`, `submissions.imageUrl`, `videoUrl`, `gameUrl`, `likesCount`
- デフォルト: `user_meta.lotteryBonusCount=0`, `user_meta.cardsAlbum=[]`, `user_meta.notifications=[]`, `submissions.jpResult='none'`, `submissions.likesCount=0`, `timestamps: createdAt/updatedAt` 自動


