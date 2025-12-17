# クリーンアップ・リファクタリング完了サマリー

## 削除したファイル・ディレクトリ

### Node.js/Express関連
- `backend/src/` - Node.js/Expressサーバーのソースコード
- `backend/models/` - Mongooseモデル（TypeScript/JavaScript）
- `backend/dist/` - コンパイル済みファイル
- `backend/node_modules/` - Node.js依存関係
- `backend/package.json` - Node.jsパッケージ設定
- `backend/package-lock.json` - Node.js依存関係ロックファイル
- `backend/tsconfig.json` - TypeScript設定
- `backend/public/` - Node.js用のpublicディレクトリ（一部は残存）

### Next.js関連
- `frontend/` - Next.jsフロントエンド全体

### Docker関連
- `backend/Dockerfile` - 古いNode.js用Dockerfile（削除）
- `backend/Dockerfile.django` - Django用Dockerfile（`Dockerfile`にリネーム）
- `docker-compose.yml.old` - 古いdocker-composeファイル
- `docker-compose.prod.yml` - 古いNode.js/MongoDB用の本番設定
- `docker-compose.dev.yml` - 古いNode.js/MongoDB用の開発設定

### その他
- `backend/README.md` - 古いREADME（`README_DJANGO.md`がメイン）

## 更新したファイル

### Docker設定
- `backend/docker-compose.yml` - `Dockerfile.django`参照を`Dockerfile`に変更
- `backend/Dockerfile` - `Dockerfile.django`の内容をコピーして作成

### ドキュメント
- `backend/README_DJANGO.md` - docker-composeコマンドの参照を更新（`-f docker-compose.prod.yml`を削除）

## 現在のプロジェクト構成

```
toybox/
├── backend/              # Django バックエンド
│   ├── users/           # ユーザー認証・プロフィール
│   ├── submissions/     # 投稿機能
│   ├── lottery/         # 抽選・報酬処理
│   ├── gamification/    # 称号・カード収集
│   ├── sharing/         # Discordシェア
│   ├── adminpanel/      # 管理画面UI
│   ├── frontend/        # 一般UI（Djangoテンプレート）
│   ├── docker-compose.yml
│   ├── Dockerfile        # Django用（旧Dockerfile.django）
│   ├── Dockerfile.prod   # 本番用Django
│   └── README_DJANGO.md  # メインREADME
├── docs/                 # 移行ドキュメント
├── doc/                  # その他のドキュメント
│   └── legacy/          # Django移行前のコード（アーカイブ）
└── scripts/              # ユーティリティスクリプト
```

## 技術スタック

- **Backend**: Django 5 + DRF + PostgreSQL + Celery + Redis
- **Frontend**: Django Templates（HTMX対応）
- **Database**: PostgreSQL（MongoDBから移行済み）
- **Queue**: Celery + Redis（BullMQから移行済み）

## 注意事項

- `backend/scripts/mongo_to_pg.py` - MongoDBからPostgreSQLへの移行スクリプトは残しています（参考用）
- `doc/legacy/` - 古いコードはアーカイブとして残しています
- `backend/public/uploads/` - アップロードファイルは残しています（必要に応じて整理）















