## ToyBox Monorepo

ToyBox は Next.js(Frontend) と Node.js/Express(Backend) の TypeScript モノレポです。段階的な実装で、まずはファイル定義とコアロジックから構築します。

### 技術スタック
- **Frontend**: Next.js, React, Tailwind CSS, NextAuth.js (導入予定)
- **Backend**: Express, Mongoose (MongoDB), BullMQ + ioredis, Jest, ts-jest, TypeScript

### ディレクトリ構成
```text
toybox-app/
  backend/
    package.json
    tsconfig.json
    models/
      Submission.ts
      UserMeta.ts
    src/
      server.ts
      services/
        lotteryService.ts
  frontend/
    package.json
    tsconfig.json
    tailwind.config.js
```

## 前提
- Node.js (推奨: v18+)
- MongoDB (ローカル or クラウド)
- Redis（BullMQ を利用する場合）

## セットアップ（初回のみ）
PowerShell 例:
```powershell
# 依存関係のインストール
cd toybox-app\backend; npm i
cd ..\frontend; npm i
```

## 環境変数（Backend）
`toybox-app/backend/.env` を作成:
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
cd toybox-app\backend
npm run dev

# Terminal 2 (Frontend)
cd toybox-app\frontend
npm run dev
```
- Backend: http://localhost:4000/health
- Frontend: http://localhost:3000 （Next.js デフォルト）

## ビルド/実行/テスト（Backend）
```powershell
cd toybox-app\backend
npm run build   # tsc
npm start       # node dist/index.js
npm test        # jest
```

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
