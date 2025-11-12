### 旧API → DRF 互換レイヤー計画

目的: フロントの変更最小化で段階移行。Express の `/api/**` と同一パス/同等スキーマを DRF で提供し、移行期間はリバースプロキシで段階的に切替える。


## 1) ルーティング互換（パス設計）
- DRF 側で以下のパスをそのまま提供（先頭 `/api` を維持）。
  - 認証: `/api/auth/register|login|logout|me|deleteAccount`, `/api/auth/discord/login|callback`（必要なら中継）
  - マイページ: `/api/contact`, `/api/topic/work|play|fetch`, `/api/feed`, `/api/submissions/me`, `/api/notifications`, `/api/notifications/read`, `/api/user/profile/:anonId`, `/api/user/submissions/:anonId`, `/api/submissions/:id`, `/api/submissions/:id/like`
  - ユーザー: `/api/user/me|nextTitle|profile/*`（bio/name/upload/avatar/header/patch）
  - 提出: `/api/submit`, `/api/submit/upload`
  - カード: `/api/cards/generate|me|summary`
  - 監視: `/health`, `/ready`, `/metrics`（アプリ/インフラに応じ再現または代替提供）
- Next.js サーバールート `/api/share/discord` は選択肢:
  - A) 当面据置（フロント内に保持）。
  - B) DRF `/api/share/discord` を追加し、Bot 投稿と履歴保存を DRF 側へ移管。


## 2) レスポンス互換（シリアライザ）
- 既存 DTO 相当の DRF Serializer を作成。フィールド名/型を合わせる。
  - 例: `UserMeSerializer`, `UserProfileSerializer`, `FeedItemSerializer`, `SubmissionResultSerializer` 等。
- エラー整形: DRF の `EXCEPTION_HANDLER` を差し替え、`{ status, code, message, details }` 形式へ正規化（Zod→DRF バリデーション差異は DRF 側で詳細を `details` に格納）。


## 3) 認証/認可の互換
- SimpleJWT（または django-rest-knox）で JWT を発行。HttpOnly Cookie（`token`）/`Authorization: Bearer` 両対応。
- `optionalAuth` 相当: カスタムミドルウェアで `request.user` が匿名ならスキップ、いれば解決。
- `requireAnonAuth` 相当: `request.user` から `anon_id` を引き、認可が必要なビューでは必須にする。
  - モデル: `User(anon_id, email?, username?, display_name, password_hash)` を PostgreSQL に再設計。


## 4) レート制限の互換
- DRF Throttling（`AnonRateThrottle`/`UserRateThrottle` を拡張）で「書込のみ 120/min」。
- キー関数: `anon:<anon_id>` 優先、なければ `ip:<addr>` を返すカスタムスコープで実装。
- レスポンスヘッダ: 互換ヘッダ（`X-RateLimit-*`, `Retry-After`）をカスタムミドルウェアで付与。


## 5) ログ/メトリクス
- ログ: JSON 1行の構造化ログ（`request.start/end`, `request.error`）を DRF ミドルウェアで再現。
- メトリクス: `/metrics` は `django-prometheus` 等で代替し、メトリクス名の互換を保つ（必要に応じて rename）。


## 6) データモデル移行（Mongo → PostgreSQL）
- 正規化案
  - `users` → `users`（unique: email?, username?, anon_id）。
  - `user_meta` → `user_profiles`（1:1, display_name/bio/avatar_url/header_url/active_title/active_title_until/bonus_count）。
  - `cardsAlbum[]` → `user_cards(user_id, card_id, obtained_at)`。
  - `likedSubmissionIds[]` → `likes(user_id, submission_id)`（unique 複合制約）。
  - `notifications[]` → `notifications(user_id, type, message, submission_id?, from_user_id?, created_at, read)`。
  - `submissions` → `submissions(id, user_id, aim, step1..3, frame_type, image_url?, video_url?, game_url?, likes_count, created_at, updated_at)`。
  - `jackpotwins` → 廃止（必要時のみ `jackpot_wins` へ移設）。
- マスタデータ: `cards_master` をテーブル化（もしくは従来通りファイル→アプリ読込のままでも可）。
- 参照: `anon_id` はユーザーテーブルに保持、結合は `user_id` 主体へ移行。


## 7) 段階移行プラン
- Phase 0（準備）
  - DRF プロジェクト雛形、共通例外ハンドラ/ログ/スロットルを導入。
  - モデル/マイグレーションを定義し、Mongo→Pg ETL（抜粋/匿名化データで検証）。

- Phase 1（プロキシ併用）
  - リバースプロキシ（Caddy/Nginx）で `/api` を旧/新にパスベース振り分け（まずは`/health|/ready|/metrics`と読み取り系から）。
  - 影ログ/シャドウトラフィックで差分検証（レスポンスコード/本文サイズ/主要フィールド）。

- Phase 2（読み取り系の切替）
  - `/api/feed`, `/api/user/profile/:anonId`, `/api/user/submissions/:anonId`, `/api/submissions/:id` を DRF へ切替。
  - いいね状態/通知件数の計算互換を確認。

- Phase 3（書き込み系の切替）
  - `/api/submit`, `/api/submit/upload`, `/api/submissions/:id/like(POST|DELETE)`, `/api/user/profile/*` などを段階的に切替。
  - スロットル/バリデーション/エラー JSON の互換を監視。

- Phase 4（認証の切替）
  - `/api/auth/*` を DRF に切替（JWT Cookie 運用を維持）。
  - ログアウト/削除フローで関連データの消し込みを DRF 実装へ移行（監査ログ追加）。

- Phase 5（周辺/撤去）
  - Discord シェアを DRF 実装に統合し、投稿履歴をテーブル化（任意）。
  - 旧 Express/Mongo の停止とスナップショット保管、最終クリーンアップ。


## 8) 互換テーブル（抜粋）

| 旧（Mongo） | 新（PostgreSQL） | 備考 |
|---|---|---|
| users.email/username unique（部分） | users(email, username) unique（nullable で実現） | NULL は一意制約対象外 |
| user_meta.cardsAlbum[] | user_cards(user_id, card_id, obtained_at) | 取得履歴の正規化 |
| user_meta.likedSubmissionIds[] | likes(user_id, submission_id) unique | 集計は `COUNT(*)` |
| user_meta.notifications[] | notifications(...) | 配列→明細行 |
| submissions.steps[3] | submissions.step1..step3 | 配列→列展開（JSON配列でも可） |
| jackpotwins | 廃止 or jackpot_wins | 機能が無効化のため省略可 |


## 9) リスク低減策
- レスポンススナップショット比較（主要 API を日次で記録）。
- 互換テスト（ヘッダ/ボディ/ステータス/スロットルヘッダ）。
- フィーチャートグル（DRF/旧API スイッチ）と段階的ロールアウト（1%→25%→100%）。
- 障害時の即時ロールバック（プロキシ切替/環境変数で無停止切替）。


