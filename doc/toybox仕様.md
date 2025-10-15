## ToyBox 開発プロンプト（フェーズ分割ガイド）

複雑なフルスタック開発を、エラーを回避するために細かくフェーズ分けし、一歩ずつ進めます。特にエラーが出やすい外部コマンド（npm install 等）は最初は避け、まずファイル作成・定義作業に集中します。各ステップは Cursor の処理が完了してから次に進んでください。

## 前提
- **Agent**: 汎用チャットモード (General Chat Mode)
- **LLM**: GPT-4o または Claude 3 Opus
- **実行環境**: 空のフォルダ `toybox-app` を開いた状態
- **技術スタック**: Node.js (Express) + Next.js (TypeScript)

## ステップ 1: プロジェクトのディレクトリと設定ファイルの作成
AI が裏側で実行する可能性のある `npm install` や `npx create-next-app` など、失敗しやすい外部コマンドの実行を避け、まずはファイルを作成することに集中します。

### プロンプト #1
現在開いているフォルダ内に、Next.js と Node.js (Express) を組み合わせた TypeScript のモノレポ構造を作成してください。外部コマンドは不要で、ファイルを作成するだけで構いません。

- **生成ディレクトリ**
  - `backend/`（Node.js/Express サーバーのルート）
  - `frontend/`（Next.js プロジェクトのルート）
- **生成ファイル**
  - `backend/package.json`: TypeScript、Express、Mongoose、BullMQ（ジョブキュー）、Jest（テスト）に必要な依存関係の基本設定
  - `frontend/package.json`: Next.js、React、NextAuth.js、Tailwind CSS、TypeScript に必要な依存関係の基本設定
  - `backend/tsconfig.json` と `frontend/tsconfig.json` の適切な設定
  - `frontend/tailwind.config.js`: スチームパンク調（茶・金・濃灰など）のカスタムカラースキーム

```text
backend/
  package.json
  tsconfig.json
frontend/
  package.json
  tsconfig.json
  tailwind.config.js
```

## ステップ 2: データベーススキーマとサーバー初期化
アプリケーションの核となるデータ構造を定義します。

### プロンプト #2
ステップ1で作成したファイルを参照・利用してください。

- **データベーススキーマ**（`backend/models/`）
  - `Submission.ts`: 提出物。フィールドに以下を含むこと
    - `submitterAnonId`（固定匿名ID）
    - `aim`（ねらい100字）
    - `steps`（再現手順3行）
    - `jpResult`（抽選結果: `'win'|'lose'|'none'`）
    - `frameType`（フレーム種別）
    - 添付資料の要件にある全フィールドを正確に含める
  - `UserMeta.ts`: ユーザー付随情報
    - `anonId`, `lotteryBonusCount`, `cardsAlbum`, `activeTitle`（称号） など
- **サーバーの基本構造**
  - `backend/src/server.ts`: Express 初期化、MongoDB(Mongoose) 接続、CORS/JSON ミドルウェア設定

## ステップ 3: ジャックポット抽選と報酬ロジックの実装
最も複雑で重要なビジネスロジックをサーバー側で実装します。

### プロンプト #3
ステップ2で作成したスキーマ（`Submission.ts`、`UserMeta.ts`）を参照し、以下を `backend/src/services/lotteryService.ts` に実装してください。

- **抽選確率計算関数**: 連続未当選回数 `k` を受け取り、確率 \(P_{final} = \min(0.008 + 0.002 \times k, 0.05)\) を返す
- **提出後の全処理関数**: ユーザーIDと提出データを受け取り、
  - 1日1回の提出制限チェック
  - 上記確率に基づくジャックポット抽選の実行
  - 抽選結果に応じた `lotteryBonusCount` の更新（当選時はリセット、非当選時はインクリメント）
- **即時報酬付与関数**: 抽選結果とは独立して、ランダムな称号付与（7日間期限付き）と、コレクションカード1枚配布（アルバムに格納）

## ステップ 4: 認証と API エンドポイントの実装
フロントエンドが利用する API と、セキュリティの基盤となる認証を実装します。

### プロンプト #4
ステップ3で作成したサービス関数を参照し、`backend/src/api/submit.ts` に以下を実装してください。

- **POST `/api/submit`**
  - 認証ミドルウェアを通したユーザーから提出データを受け取る
  - `lotteryService` の関数を呼び出し、提出・抽選・報酬付与を実行
  - 抽選結果と付与された報酬（称号名、カードID）を含む JSON を返却
- **GET `/api/user/me`**
  - ログインユーザーの固定匿名ID、現在の称号、カードアルバム、提出ストリークを返す

## ステップ 5: フロントエンド UI の基本構築と連携
Next.js/React に、提出フォーム UI とバックエンド API の呼び出しを実装します。

### プロンプト #5
- **提出フォームコンポーネント**: `frontend/components/SubmitForm.tsx`
  - タイトル、ねらい100字、再現手順3行、求人ひもづけ一言の入力フィールド
- **API 連携**: 送信時に `POST /api/submit` を呼び出し、結果を受け取る
- **報酬表示モーダル**: 提出成功後、返却データに基づきジャックポット結果と即時報酬（称号、カード）を表示
  - デザインは Tailwind CSS でスチームパンク調（茶・金・濃灰のカラーパレット）



