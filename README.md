# ToyBox

Django 5 + DRF + PostgreSQL + Celery + Redis 構成のWebアプリケーション

## プロジェクト構成

- **Backend**: Django 5 + DRF + PostgreSQL + Celery + Redis
- **Frontend**: Django Templates（HTMX対応）

## クイックスタート

### Dockerでの起動（推奨）

```bash
cd backend
docker compose up -d
```

詳細は [backend/README_DJANGO.md](./backend/README_DJANGO.md) を参照してください。

## ドキュメント

- **開発ガイド**: [backend/README_DJANGO.md](./backend/README_DJANGO.md)
- **移行ドキュメント**: [docs/migration/](./docs/migration/)
- **レガシーコード**: [doc/legacy/](./doc/legacy/)（Django移行前のコード）
- **デプロイメント**: [doc/deployment/](./doc/deployment/)
- **セットアップ**: [doc/setup/](./doc/setup/)

## ディレクトリ構成

```
toybox/
├── backend/              # Django バックエンド
│   ├── users/           # ユーザー認証・プロフィール
│   ├── submissions/     # 投稿機能
│   ├── lottery/         # 抽選・報酬処理
│   ├── gamification/    # 称号・カード収集
│   ├── sharing/         # Discordシェア
│   ├── adminpanel/      # 管理画面UI
│   └── frontend/         # 一般UI（Djangoテンプレート）
├── docs/                 # 移行ドキュメント
├── doc/                  # その他のドキュメント
│   ├── legacy/          # Django移行前のコード
│   ├── deployment/      # デプロイメント関連
│   ├── setup/           # セットアップ関連
│   └── troubleshooting/ # トラブルシューティング
└── scripts/              # ユーティリティスクリプト
```
