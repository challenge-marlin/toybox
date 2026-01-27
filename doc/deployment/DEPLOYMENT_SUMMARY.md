# 自動デプロイ設定完了

## ✅ 実装内容

### 1. GitHub Actionsワークフロー
- **ファイル**: `.github/workflows/deploy.yml`
- **機能**: `main`ブランチへのプッシュで自動デプロイ
- **手動実行**: GitHub ActionsのUIからも実行可能

### 2. デプロイスクリプト
- **ファイル**: `scripts/deploy.sh`
- **機能**: ローカルから手動でデプロイを実行
- **使用方法**: `./scripts/deploy.sh`

### 3. ドキュメント
- **SETUP_DEPLOYMENT.md**: 初回セットアップ手順
- **DEPLOYMENT_GUIDE.md**: 詳細なデプロイガイド
- **DEPLOYMENT.md**: デプロイ概要（更新済み）
- **README.md**: 自動デプロイの説明を追加（更新済み）

## 📋 セットアップ手順（初回のみ）

### ステップ1: VPS側でSSH鍵を生成

```bash
# VPSサーバーで実行
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ""
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
cat ~/.ssh/github_actions_deploy  # 秘密鍵を表示（次のステップで使用）
```

### ステップ2: GitHub Secretsに登録

GitHubリポジトリの **Settings** → **Secrets and variables** → **Actions** で以下を追加：

1. **VPS_HOST**: `160.251.168.144`
2. **VPS_USER**: `app`
3. **VPS_SSH_PRIVATE_KEY**: ステップ1で表示された秘密鍵の内容（全部）

### ステップ3: VPS側でプロジェクトを初期化

```bash
mkdir -p ~/toybox
cd ~/toybox
git clone https://github.com/challenge-marlin/toybox.git .
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env
# .envファイルを編集
```

### ステップ4: 初回デプロイ

```bash
# ローカルで
git add .
git commit -m "Setup automatic deployment"
git push origin main
```

## 🚀 使用方法

### 通常のデプロイフロー

1. **ローカルでコードを編集**
2. **変更をコミット**
   ```bash
   git add .
   git commit -m "機能追加: ..."
   ```
3. **GitHubにプッシュ**
   ```bash
   git push origin main
   ```
4. **自動デプロイ開始**
   - GitHub Actionsが自動的に実行される
   - VPSにSSH接続して最新コードを取得
   - Docker Composeで再ビルド・再起動

### デプロイの確認

- **GitHub Actions**: リポジトリの **Actions** タブで確認
- **VPS側**: `docker compose ps` でコンテナの状態を確認

## 📁 ファイル構成

```
toybox/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actionsワークフロー
├── scripts/
│   └── deploy.sh                # 手動デプロイスクリプト
├── SETUP_DEPLOYMENT.md          # 初回セットアップ手順
├── DEPLOYMENT_GUIDE.md          # 詳細デプロイガイド
├── DEPLOYMENT.md                 # デプロイ概要（更新済み）
└── README.md                     # プロジェクト概要（更新済み）
```

## 🎯 次のステップ

1. **VPS側でSSH鍵を生成**（上記ステップ1）
2. **GitHub Secretsに登録**（上記ステップ2）
3. **VPS側でプロジェクトを初期化**（上記ステップ3）
4. **初回デプロイを実行**（上記ステップ4）

これで、**ローカルで編集 → コミット → プッシュ**するだけで、本番環境に自動的に反映されます！

## 📚 参考ドキュメント

- **SETUP_DEPLOYMENT.md**: 初回セットアップの詳細手順
- **DEPLOYMENT_GUIDE.md**: デプロイの詳細ガイドとトラブルシューティング
- **DEPLOYMENT.md**: デプロイの概要

