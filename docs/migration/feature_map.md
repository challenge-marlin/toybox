### 機能マッピング（現行 → Django/DRF）

対象: 一般機能・管理機能の実装状況と挙動の癖を整理し、DRF での受け皿を定義する。


## 一般機能

- 投稿フロー
  - 現行: 画像/動画を先に `/api/submit/upload` でアップロード → `/api/submit` に aim/steps/frameType と URL を送信。ゲームは ZIP を展開して `gameUrl` を返し、同様に `/api/submit`。
  - 挙動: 直近10秒の同一内容を重複スキップ。投稿保存後に「抽選」は行わず、称号/カードの即時付与のみ。
  - いいね: `/api/submissions/:id/like` POST/DELETE（集計 `likesCount` をカウントアップ/ダウン、通知作成）。

- コメント ON/OFF
  - 現行: コメント機能なし（OFF）。

- 称号/色
  - 現行: `activeTitle`（7日有効, `activeTitleUntil`）。色指定は無し。
  - 付与: `POST /api/user/nextTitle` または投稿時の即時報酬。失効時は自動クリア（レスポンス側で期限チェック）。

- 抽選
  - 現行: 無効化（`jpResult = 'none'` 固定）。ロジック痕跡・レガシーモデル `JackpotWin` は残存。

- ピン固定
  - 現行: 未実装。

- カード収集
  - 現行: マスタ（TSVロード）からランダム配布。アルバムは `user_meta.cardsAlbum[]` に `{ id, obtainedAt }`。所持一覧・要約 API あり。

- ToyBoxDay 表示（お題）
  - 現行: `/api/topic/work|play` で日替わり、`/api/topic/fetch?type=...` で外部サイトから抽出も可。

- フィード
  - 現行: `/api/feed` 降順ページング（`createdAt` ベース, cursor=ISO）。`user_meta` を join 的にまとめて取得。

- プロフィール/マイページ
  - 現行: `GET /api/user/me`, `PATCH /api/user/profile`, 画像アップロード, 公開プロフィール, 自分/他人の提出一覧, 通知一覧/既読, Web Vitals/FE 計測の集計受け口。

- 連携（Discord シェア）
  - 現行: Next.js サーバールート `/api/share/discord` が Discord Bot API へ直接投稿（20MB制限/リトライ有）。履歴のDB保持は無し。


## 管理機能

- ユーザー情報・パスワード再設定
  - 現行: ユーザー登録/ログイン/ログアウト/`/auth/me`。パスワード再設定フローは無し。

- 登録情報（プロフィール/称号など）
  - 現行: 自己更新 API のみ。管理側の一括編集/監査ログは無し。

- カード情報
  - 現行: 付与はアプリロジック側。マスタはアプリ同梱（DB外）。管理UI無し。

- 投稿履歴（削除後も保持）
  - 現行: 投稿削除はハードデリート（`deleteOne`）。削除後保持は無し。

- 投稿一覧
  - 現行: 一般取得 API のみ（管理向けの高度な検索・モデレーションUI無し）。

- Discord シェア履歴
  - 現行: なし（サーバールート→Discord直投稿、DBに履歴を保持しない）。

- 警告発行、停止・BAN・削除
  - 現行: なし。`/auth/deleteAccount` は本人による削除のみ（`Submission`/`UserMeta`/`User` を削除）。


## パリティリスク一覧

| 機能名 | 現状の癖 | 懸念 | 対応方針 |
|---|---|---|---|
| 認証/JWT | Cookie/Authorization 両対応、`optionalAuth`+`requireAnonAuth` の二段構え | DRF の認証方式差異（Session/Cookie/JWT）で互換崩れ | DRF SimpleJWT を Cookie 運用。匿名IDはユーザーテーブルに保持し、認可で解決 |
| レート制限 | 書込のみ 120/min（anon or IP） | DRF への移行でルール差異 | DRF の Throttle でキー関数を `anonId or IP` に合わせ実装 |
| エラー整形 | `AppError`/Zod/アップロード/Mongoose の正規化 | 例外表現/コードが変わる | DRF の ExceptionHandler をカスタムし同等 JSON 形へ |
| 投稿削除 | ハードデリート | 監査/復元不可 | 論理削除（`deleted_at`,`deleted_by`）＋監査テーブル導入 |
| いいね | `user_meta.likedSubmissionIds` に配列保持 | RDB 正規化と一意制約が必要 | `likes (user_id, submission_id)` テーブルでユニーク制約 |
| カード | マスタはファイル、アルバムは配列埋め込み | 参照整合性/検索性 | `cards_master`（参照用）＋`user_cards`（取得履歴）に正規化 |
| 称号 | 期限切れをレスポンス時にクリア | 一貫性（DBと表示） | バックグラウンド/DBトリガやビューで有効レコードのみを返す |
| 抽選 | 無効化（`none` 固定） | 将来の仕様変更で差分増 | DRF 側はユースケース層でスイッチ対応 |
| Discord シェア | フロントのサーバールート直投げ | 監査/再送/失敗追跡なし | DRF に `/share/discord` を実装し履歴（status, messageId, size）を保存 |
| アップロード | `/uploads` 直配信、サイズ/拡張子制限は Multer | S3/クラウド化で差分 | DRF + S3 直 PUT（署名URL）へ段階移行 |
| 外部お題取得 | スクレイピング依存 | 変更に脆弱 | コンテンツ管理化/キャッシュ層で安定化 |


