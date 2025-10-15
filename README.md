## ToyBox Monorepo

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
  start-all-docker.bat
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
cd C:\Users\<あなたの名前>\toybox
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
