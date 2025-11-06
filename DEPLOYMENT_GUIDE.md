# 自動デプロイガイド

## 概要

GitHubにプッシュするだけで、自動的に本番環境（VPS）にデプロイされます。

## セットアップ手順

### 1. VPS側での準備

#### SSH鍵の生成

VPSサーバー（VNCコンソールまたは既存の接続方法）で実行：

```bash
# appユーザーでSSH鍵を生成（既に存在する場合はスキップ）
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions_deploy

# 公開鍵をauthorized_keysに追加
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 秘密鍵を表示（これをGitHub Secretsに登録します）
cat ~/.ssh/github_actions_deploy
```

#### プロジェクトの初期セットアップ

```bash
# プロジェクトディレクトリを作成
mkdir -p ~/toybox
cd ~/toybox

# Gitリポジトリをクローン（まだの場合）
git clone https://github.com/challenge-marlin/toybox.git .

# 環境変数ファイルを作成
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env

# .envファイルを編集（必要な環境変数を設定）
vi backend/.env
vi frontend/.env
```

### 2. GitHub Secretsの設定

GitHubリポジトリの設定ページで以下を追加：

1. **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

以下のシークレットを追加：

| Name | Value | 説明 |
|------|-------|------|
| `VPS_HOST` | `160.251.168.144` | VPSサーバーのIPアドレス |
| `VPS_USER` | `app` | SSH接続するユーザー名 |
| `VPS_SSH_PRIVATE_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | VPSで生成した秘密鍵の内容（全部） |

#### VPS_SSH_PRIVATE_KEYの取得方法

VPSサーバーで：

```bash
cat ~/.ssh/github_actions_deploy
```

表示された内容を**全部**コピーして、GitHub Secretsの`VPS_SSH_PRIVATE_KEY`に貼り付けます。

### 3. 初回デプロイ

#### 方法A: 自動デプロイ（推奨）

```bash
# ローカルで変更をコミット
git add .
git commit -m "Setup automatic deployment"
git push origin main
```

`main`ブランチにプッシュすると、自動的にデプロイが開始されます。

#### 方法B: 手動デプロイ

GitHub Actionsのページから手動で実行することもできます：

1. **Actions**タブを開く
2. **Deploy to Production**ワークフローを選択
3. **Run workflow**ボタンをクリック

#### 方法C: ローカルから手動実行

```bash
# 環境変数を設定
export VPS_HOST=160.251.168.144
export VPS_USER=app
export SSH_KEY=~/.ssh/id_rsa

# デプロイスクリプトを実行
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## デプロイの流れ

1. **GitHubにプッシュ** → `main`ブランチに変更をプッシュ
2. **GitHub Actionsが起動** → 自動的にワークフローが実行される
3. **VPSにSSH接続** → GitHub ActionsがVPSサーバーに接続
4. **コードを取得** → `git fetch`と`git reset`で最新のコードを取得
5. **コンテナを再ビルド** → `docker compose up -d --build`で再起動
6. **ヘルスチェック** → デプロイが成功したか確認

## トラブルシューティング

### デプロイが失敗する場合

#### SSH接続エラー

```bash
# VPS側でSSH鍵の権限を確認
chmod 600 ~/.ssh/github_actions_deploy
chmod 700 ~/.ssh

# SSH接続をテスト
ssh -i ~/.ssh/github_actions_deploy localhost
```

#### Docker Composeエラー

```bash
# VPS側でログを確認
cd ~/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

#### 環境変数エラー

```bash
# .envファイルが存在するか確認
ls -la backend/.env
ls -la frontend/.env

# 環境変数が正しく設定されているか確認（パスワードなどは表示しない）
grep -v "PASSWORD\|SECRET\|KEY" backend/.env
```

### 手動でロールバック

```bash
# VPS側で実行
cd ~/toybox
git log --oneline -10  # 過去のコミットを確認
git reset --hard <コミットハッシュ>  # ロールバックしたいコミット
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## セキュリティ注意事項

1. **SSH鍵の管理**
   - 秘密鍵は絶対にGitHubリポジトリにコミットしない
   - GitHub Secretsにのみ保存
   - 定期的に鍵をローテーション

2. **環境変数**
   - `.env`ファイルは`.gitignore`に含まれていることを確認
   - 本番環境の`.env`は手動で管理

3. **アクセス制限**
   - VPSのファイアウォールでSSHポート（22）へのアクセスを制限
   - 必要に応じてGitHub ActionsのIPアドレスを許可リストに追加

## デプロイの確認

### GitHub Actionsのログを確認

1. GitHubリポジトリの**Actions**タブを開く
2. 最新のワークフロー実行をクリック
3. ログを確認してエラーがないかチェック

### VPS側で確認

```bash
# コンテナの状態を確認
cd ~/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# ログを確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# ヘルスチェック
curl http://localhost/health
curl https://toybox.ayatori-inc.co.jp/health
```

## まとめ

- ✅ GitHubにプッシュするだけで自動デプロイ
- ✅ 手動実行も可能
- ✅ ヘルスチェック付き
- ✅ ログで状況を確認可能

これで、ローカルで編集 → コミット → プッシュするだけで、本番環境に自動的に反映されます！

