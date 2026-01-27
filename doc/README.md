# ドキュメント

このディレクトリには、プロジェクトのドキュメントが整理されています。

## 構成

### ルート直下（仕様・概要）

- `toybox仕様.md` - TOYBOX仕様
- `TOYBOX概要書.md` - 概要書
- `カード情報.md` - カード情報
- `作業工程.md` - 作業工程

### サブディレクトリ

- **`deployment/`** - デプロイ・ホスティング
  - WinSCP手順（`DEPLOY_今日の変更_WinSCP手順.md`）、デプロイガイド、VAR_WWW 構築、バージョンアップ、SSO/StudySphere アップロード一覧、`ホスティング.md` など

- **`setup/`** - セットアップ
  - セットアップ手順、SSH/VNC、Docker/Caddy作成、venv、StudySphere連携、`setup-on-server.txt` など

- **`troubleshooting/`** - 障害対応・トラブルシュート
  - 502/Caddy/Nginx、接続拒否、SSO 502、ネットワーク診断、インシデント報告、復元手順、各種 FIX ガイドなど

- **`backup/`** - バックアップ
  - バックアップ実装・戦略・復元テスト、ローカルテスト、PostgreSQL二重バックアップの理由 など（TXT）

- **`mail/`** - メール
  - メール送信チェックリスト、メール通知設定ガイド（TXT）

- **`reference/`** - その他・参照
  - Discord通知、システム構成図、やることリスト、リファクタリングサマリー、現状・デバッグメモ など

- **`legacy/`** - 旧実装（参考用）
  - Django移行前のコードなど

## 移行・実装

- **Backend**: [backend/README_DJANGO.md](../backend/README_DJANGO.md)
- **移行ドキュメント**: [docs/migration/](../docs/migration/)
