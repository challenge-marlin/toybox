## ToyBox Monorepo

### 起動方法（クイック）
- Windows のバッチで一括起動
  - `start-all-docker.bat`（Docker Desktop 必須）
  - 停止: `stop-all-docker.bat`
- 直接コマンド（推奨）
  - `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build`
  - 画面: Frontend `http://localhost:3000/` / Backend `http://localhost:4000/health`

### 環境変数ファイル（.env）

はじめに、見本をコピーして値を編集してください。

```bash
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env
```

主な設定ポイント:

- Backend (`backend/.env`)
  - `CORS_ORIGINS`: 許可するフロントのオリジン（例: `https://toybox.example.com`）
  - `JWT_SECRET`: 本番では十分長い乱数に変更
  - `MAX_UPLOAD_MB_*`: 種別ごとのアップロード上限

- Frontend (`frontend/.env`)
  - `NEXT_PUBLIC_API_BASE`: バックエンドの公開URL（例: `http://localhost:4000` or `https://api.toybox.example.com`）
  - `BACKEND_INTERNAL_URL`（任意）: SSR/ビルド時の内部到達先（例: `http://backend:4000`）
  - `NEXT_PUBLIC_SITE_URL`（任意）: サイトのフルURL（OGP向け）

### カード画像とフレーム表示（実装済み）
- 置き場所/URL
  - カード画像: `/uploads/cards/<ファイル名>`（例: `/uploads/cards/C001.png`）
  - フレーム画像: `/uploads/cards/frame.png`
  - 推奨配置先: `backend/public/uploads/cards/`（Docker dev では実体はコンテナ内 `/app/public/uploads/cards`）

- 命名
  - 既存ミニセット: `C001.png`, `E001.png` など
  - 数値運用時: キャラ `1.png`〜`20.png`、エフェクト `101.png`〜`140.png`

- フロント実装（フレーム重ね＋3%縮小、すべて `object-contain`）
  - `frontend/src/components/CardReveal.tsx`
    - ベース画像: `absolute inset-0 w-full h-full object-contain` + `scale(0.97)`
    - フレーム: `absolute inset-0 w-full h-full object-contain pointer-events-none`
  - `frontend/src/app/collection/page.tsx`
    - 各カードの表示領域（`relative aspect-[2/3] ...`）にフレームを重ね、画像は `scale(0.97)` で中央縮小
  - `frontend/src/app/profile/view/page.tsx`
    - 所持カードをコレクションと同一表示（フレーム重ね、3%縮小）。初回処理で得た画像のみを使用

- 開発時の注意（Docker dev）
  - `docker-compose.dev.yml` で `uploads` ボリュームが `/app/public/uploads` にマウントされています
  - ローカルに置いただけでは反映されないため、必要に応じてコンテナにコピーしてください

ToyBox は Next.js(Frontend) と Node.js/Express(Backend) の TypeScript モノレポです。段階的な実装で、まずはファイル定義とコアロジックから構築します。

### 技術スタック
- **Frontend**: Next.js, React, Tailwind CSS, NextAuth.js (導入予定)
- **Backend**: Express, Mongoose (MongoDB), BullMQ + ioredis, Jest, ts-jest, TypeScript

### ディレクトリ構成（抜粋）
```text
toybox/
  backend/
    package.json
    tsconfig.json
    public/
      uploads/
        cards/           # 静的配信の実体（/uploads 配下として公開）
    models/
      Submission.ts
      UserMeta.ts
    src/
      server.ts
      api/
        submit.ts
        mypage.ts
        cards.ts
      services/
        lotteryService.ts
      scripts/
        clearSubmissionImages.ts  # 提出画像の一括クリア
  frontend/
    package.json
    tsconfig.json
    src/
      app/
      components/
  docker-compose.yml
  docker-compose.dev.yml
  start-all-docker.bat
  start-backend.bat
  start-frontend-dev.bat
  stop-all-docker.bat
```

## 前提
- Node.js (推奨: v18+)
- MongoDB (ローカル or クラウド)
- Redis（BullMQ を利用する場合）

## セットアップ（初回のみ）
PowerShell 例:
```powershell
# 依存関係のインストール
cd backend; npm i
cd ..\frontend; npm i
```

## 環境変数（Backend）
`backend/.env` を作成:
```env
MONGODB_URI=mongodb://127.0.0.1:27017/toybox
MONGODB_DB=toybox
PORT=4000
# ジョブキュー利用時
REDIS_URL=redis://127.0.0.1:6379
```

（Frontend 用の認証変数は Step 4 以降で追記予定）

## 開発サーバの起動
2つのターミナルで実行:
```powershell
# Terminal 1 (Backend)
cd backend
npm run dev

# Terminal 2 (Frontend)
cd ..\frontend
npm run dev
```
- Backend: http://localhost:4000/health
- Frontend: http://localhost:3000 （Next.js デフォルト）

## E2E テスト（Playwright）

前提: フロント/バックが起動中（上の手順でOK）

実行（frontend ディレクトリで）:

```bash
cd frontend
npm run test:e2e
```

オプション:
- `E2E_BASE_URL` でベースURLを上書き可能（デフォルト `http://localhost:3000`）
- `E2E_API_BASE` でAPIのURLを上書き可能（デフォルト `http://localhost:4000`）

## 静的ファイル配信（/uploads）
- Backend が `/uploads` を `backend/public/uploads` から配信します。
- Docker 開発時はコンテナ内 `/app/public/uploads` に `uploads` ボリュームがマウントされます。
- Frontend の `next.config.js` で `^/uploads` は Backend にリライトされます。

確認:
- `http://localhost:4000/uploads/cards/frame.png` が表示されること

## ビルド/実行/テスト（Backend）
```powershell
cd backend
npm run build   # tsc
npm start       # node dist/index.js
npm test        # jest
```

## **🧩 目的**

「Docker Desktopを使って、ToyBoxを開発モードで立ち上げる」

---

## **✅ 前提チェック**

1. Docker Desktop が起動している（クジラのアイコンが表示されている）

2. プロジェクトフォルダに以下が存在している

```
docker-compose.yml
docker-compose.dev.yml
frontend/
backend/
```

---

## **🚀 手順（Windows CMD / PowerShell どちらでもOK）**

### **① プロジェクトルートへ移動**

例：

```
cd （\toyboxのあるルート）
```

`docker-compose.yml` がある場所が「ルート」です。

---

### **② 環境変数を設定（開発用プロジェクト名を固定）**

```
set COMPOSE_PROJECT_NAME=toybox
```

macOS/Linux の場合：

```shell
export COMPOSE_PROJECT_NAME=toybox
```

※これを設定しておくと、Docker Desktop 上で「toybox_frontend_1」「toybox_backend_1」のように統一管理されます。

---

### **③ コンテナを開発モードで起動**

```
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

*   `-d` は「バックグラウンド実行」

* もし初回起動でエラーが出た場合は、`--build` を付けて再試行してください：

```
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

---

### **④ 起動確認**

```
docker compose ps
```

✅ 正常なら、以下のように表示されます：

```
NAME                 STATE     PORTS
toybox-frontend-1    Up        0.0.0.0:3000->3000/tcp
toybox-backend-1     Up        0.0.0.0:4000->4000/tcp
toybox-mongo-1       Up        27017/tcp
toybox-redis-1       Up        6379/tcp
```

---

### **⑤ ブラウザでアクセス**

* **フロントエンド（Next.js）**  
   → http://localhost:3000/

* **バックエンドAPI**  
   → http://localhost:4000/health  
   （`{"status":"ok"}` が出たら正常）

---

### **⑥ ログをリアルタイムで見る（開発中に便利）**

```
docker compose logs -f --tail=100 backend frontend
```

終了するときは Ctrl + C

---

## **🧹 停止したいとき**

```
docker compose down
```

停止するだけで、データ（MongoDB や uploads フォルダ）は保持されます。

---

## 画像404のトラブルシュート（Docker 開発）
症状: `http://localhost:4000/uploads/cards/<ファイル>.png` が 404。

原因: 画像がホストではなく、コンテナ内 `/app/public/uploads/cards` に存在する必要がある。

対処（PowerShell）:
```powershell
cd C:\github\toybox
$cid = (docker compose -f docker-compose.dev.yml ps -q backend); if (-not $cid) { $cid = (docker compose ps -q backend) }
docker exec $cid sh -lc "mkdir -p /app/public/uploads/cards"
docker cp "C:\github\toybox\backend\public\uploads\cards\frame.png" "$($cid):/app/public/uploads/cards/frame.png"
docker exec $cid sh -lc "ls -l /app/public/uploads/cards | head -n 10"
```

注意:
- Linux は大文字小文字を区別します（例: `C001.png` と `c001.png` は別）
- マスターの `image_url` とファイル名を一致させてください（例: `/uploads/cards/C001.png`）

### 提出〜演出フロー（UI）
1. アップロード開始で全画面オーバーレイ（操作不可・二重防止）
2. アップロード完了（ロック解除）後に演出開始
   - カード取得 → 称号取得 → ジャックポット
3. カード画像は `rewardCard.image_url` を優先、未設定時は `/uploads/cards/<card_id>.png`

### 提出の種類と枠
- 画像: 黄色リング
- 動画: 青枠＋中央に再生アイコン（クリックでライトボックス再生）
- ゲームZIP: マゼンタ枠＋歯車ボタン（別タブで `index.html` 起動）
  - ゲーム提出物のサムネイルは、プロフィールアイコンの代わりに中央に歯車SVG＋「GAME」テキストを表示（クリックで拡大しない）

### アップロード上限
- 画像/動画: 1GB
- ゲームZIP: 1GB（`/api/submit/uploadGame`、サーバ側で展開）

## **💡 よくある質問**

| 状況 | 対処 |
| ----- | ----- |
| 「3000番ポートが使われている」 | 他のアプリ（ReactやVite）が起動しているかも → それを終了 or `docker-compose.dev.yml` の `ports` を `3001:3000` に変更 |
| 「backendが落ちる」 | `.env` の接続情報（`MONGODB_URI`など）を確認。再ビルド時に `.env` が未反映のケースもあり。 |
| 「ファイルを変更しても反映されない」 | `docker-compose.dev.yml` が正しくマウントされているか（例：`./backend:/app` があるか）確認。 |
| 「ログをまとめて見たい」 | `docker compose logs -f`（全サービスのログを一括で追う） |

---

## **🚪（オプション）完全に削除して再起動したいとき**

```
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

`-v` でボリュームも削除。DBデータが消えるので注意。

---

これでOKです。  
Docker DesktopのGUIでも、今の手順で起動した `toybox_frontend_1`・`toybox_backend_1` などが一覧に出ているはずです。

---

もしこの後、

* フロントが動いてるのにAPIが返らない

* アップロードが反映されない  
  といった症状があれば、`docker compose logs backend` の出力を貼ってもらえれば、原因を一緒に見ます。

## 実装済み（Backend）
- `models/Submission.ts`
  - `submitterAnonId`（固定匿名ID）, `aim`（最大100字）, `steps`（3行）, `jpResult`（'win'|'lose'|'none'）, `frameType`
  - 生成日時 (`timestamps`) 付き
- `models/UserMeta.ts`
  - `anonId`, `lotteryBonusCount`, `cardsAlbum`, `activeTitle`, `activeTitleUntil(7日)`
- `src/server.ts`
  - Express 初期化、CORS/JSON ミドルウェア、MongoDB 接続、`/health`
- `src/services/lotteryService.ts`
  - 抽選確率: \(P_{final}=\min(0.008+0.002\times k, 0.05)\)
  - 提出→抽選→`lotteryBonusCount` 更新（当選: 0 リセット／非当選: +1）
  - 即時報酬: ランダム称号（7日）付与 + カード1枚をアルバムに追加

## メンテナンス手順

### 提出画像（imageUrl）の一括クリア
DB 上の `Submission.imageUrl` を全件削除します。物理ファイルは削除しません。

実行前に MongoDB が起動していることを確認してください（Docker 推奨）。

```powershell
# Docker 環境
start-all-docker.bat
docker compose exec backend npm run -s clear:submission-images

# ローカル MongoDB に対して実行する場合
cd backend
set MONGODB_URI=mongodb://127.0.0.1:27017/toybox && set MONGODB_DB=toybox && npm run -s clear:submission-images
```

出力例:
```
[clearSubmissionImages] matched=42 modified=42
```

## 予定（Step 4 以降）
- API 実装（例）
  - `POST /api/submit`: 認証済ユーザーの提出を受け付け、抽選と即時報酬を返す
  - `GET /api/user/me`: 固定匿名ID、称号、カードアルバム、提出ストリークを返す
- Frontend UI（Step 5）
  - `components/SubmitForm.tsx` に提出フォーム
  - API 連携と結果モーダル表示（Tailwind でスチームパンク調）

## Tailwind カラー（概要）
- `steam.brown`: 真鍮寄りのブラウン系
- `steam.gold`: 金属的なゴールド系
- `steam.iron`: 重厚なダークグレー系

## メモ
- データは MongoDB の `toybox` DB を標準利用
- 連続未当選回数 `k` は `UserMeta.lotteryBonusCount` として管理
- 期限付き称号は `activeTitle` と `activeTitleUntil` で表現

---
不明点や追加要望があれば issue/タスク化して進めます。

---

## 機能追加（2025-10-22）

- みんなの投稿ページ（`/feed`）
  - 全ユーザーの投稿を新着順で表示、ページング対応
  - 種別ごとに枠色（画像/動画/ゲーム）、動画はライトボックス再生、ゲームは別タブ起動
  - ゲームサムネイルは歯車＋「GAME」アイコン（拡大なし）

- いいね機能
  - モデル: `Submission.likesCount`、`UserMeta.likedSubmissionIds`
  - API: `POST /api/submissions/:id/like`、`DELETE /api/submissions/:id/like`
  - 取得APIは `likesCount` と `liked`（自分が押したか）を返却
  - フロント: 各カード右下にハート＋数、楽観的トグル/失敗ロールバック

- 通知（いいね）
  - モデル: `UserMeta.notifications`（type/fromAnonId/message/createdAt/read）
  - 生成: いいね時に投稿者へ通知（自分自身は除外）。メッセージは表示名で「◯◯さんからいいねがつきました」
  - API: `GET /api/notifications?limit&offset`（未読件数 `unread` と `nextOffset` を返却）、`POST /api/notifications/read`（全件/指定index既読）
  - フロント: ヘッダーにベル＋未読バッジ、ドロップダウンで一覧表示。「もっと見る」で追加読み込み。開いたタイミングで既読化

- ゲームZIPアップロードのUI改善
  - 画像/動画と同様に「アップロード中」オーバーレイを表示
  - 完了後、カード→称号→ジャックポットの演出フローを開始

### API エンドポイント（追加/更新）

- いいね
  - `POST /api/submissions/:id/like`
  - `DELETE /api/submissions/:id/like`

- 通知
  - `GET /api/notifications?limit=10&offset=0`
  - `POST /api/notifications/read`（body: `{ indexes?: number[] }`。未指定なら全件既読）

- 取得系（拡張フィールド）
  - `GET /api/feed` → 各アイテムに `videoUrl`/`gameUrl`/`likesCount`/`liked` を含む
  - `GET /api/user/submissions/:anonId` → 各アイテムに `videoUrl`/`gameUrl`/`likesCount`/`liked` を含む
  - `GET /api/submissions/me` → 各アイテムに `videoUrl`/`gameUrl`/`likesCount`/`liked` を含む

---

## 無料ホスティング手順（Vercel + MongoDB Atlas + Cloudinary）

### 概要
- フロント: Vercel（Next.js）
- バックエンドAPI: 現行のExpressを使う場合は外部APIとして運用、将来は Next.js API Routes へ段階移行可
- ストレージ: Cloudinary（S3代替）
- DB: MongoDB Atlas（無料枠）

### 必要な環境変数（Vercel）
- `NEXT_PUBLIC_API_BASE`（フロント用。バックエンドの公開URL or 相対 `/api`）
- `MONGODB_URI`（Atlas の接続文字列）
- `MONGODB_DB`（DB名）
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### 手順（最短）
1. MongoDB Atlas で無料クラスタ作成 → 接続文字列（SRV）を取得
2. Cloudinary アカウント作成 → Cloud Name / API Key / Secret を取得
3. Vercel で `frontend/` をプロジェクトとしてインポート
4. Vercel の環境変数に上記を設定し、`vercel-build` でビルド（`frontend/package.json` に追加済み）
5. フロントからの API 呼び先 `NEXT_PUBLIC_API_BASE` をバックエンドURLに設定

### Cloudinary 連携の仕様
- `POST /api/submit/upload` は Cloudinary にアップロードし、成功時 `public_id` と `secure_url` を返す（既存互換の `imageUrl`/`videoUrl` も返却）
- `POST /api/user/profile/upload?type=avatar|header` も Cloudinary にアップロードし、保存URLをDBへ反映

### ローカルでの確認
```bash
# Backend
cd backend
export CLOUDINARY_CLOUD_NAME=xxxx
export CLOUDINARY_API_KEY=xxxx
export CLOUDINARY_API_SECRET=xxxx
npm run dev

# Frontend（APIベースURLをBackendに合わせる）
cd ../frontend
export NEXT_PUBLIC_API_BASE=http://localhost:4000
npm run dev
```
