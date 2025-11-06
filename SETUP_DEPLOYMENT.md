# 自動デプロイのセットアップ手順

## 概要

GitHubにプッシュするだけで、自動的に本番環境（VPS）にデプロイされるようになります。

## セットアップ手順（初回のみ）

### ステップ1: VPS側でSSH鍵を生成

VNCコンソールまたは既存の接続方法でVPSにアクセスし、以下を実行：

```bash
# appユーザーでログイン（またはrootユーザー）
cd ~

# SSH鍵を生成（GitHub Actions専用）
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ""

# 公開鍵をauthorized_keysに追加
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# 秘密鍵を表示（次のステップで使用します）
echo "=== 秘密鍵（これをコピーしてください） ==="
cat ~/.ssh/github_actions_deploy
echo "=== 秘密鍵ここまで ==="
```

### ステップ2: GitHub Secretsに鍵を登録

1. GitHubリポジトリにアクセス
2. **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

以下の3つのシークレットを追加：

#### 1. VPS_HOST
- **Name**: `VPS_HOST`
- **Value**: `160.251.168.144`

#### 2. VPS_USER
- **Name**: `VPS_USER`
- **Value**: `app`（または実際のユーザー名）

#### 3. VPS_SSH_PRIVATE_KEY
- **Name**: `VPS_SSH_PRIVATE_KEY`
- **Value**: ステップ1で表示された秘密鍵の内容を**全部**コピー&ペースト
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  （全部の内容）
  -----END OPENSSH PRIVATE KEY-----
  ```

### ステップ3: VPS側でプロジェクトを初期化

```bash
# プロジェクトディレクトリを作成
mkdir -p ~/toybox
cd ~/toybox

# Gitリポジトリをクローン（まだの場合）
git clone https://github.com/challenge-marlin/toybox.git .

# 環境変数ファイルを作成
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env

# .envファイルを編集（本番環境用の値を設定）
vi backend/.env
# 以下を設定:
# - MONGODB_URI
# - MONGODB_DB
# - REDIS_URL
# - JWT_SECRET（強力なランダム文字列）
# - CORS_ORIGINS

vi frontend/.env
# 必要に応じて設定
```

### ステップ4: 初回デプロイ

#### 方法A: GitHubにプッシュ（自動デプロイ）

```bash
# ローカルで変更をコミット
git add .
git commit -m "Setup automatic deployment"
git push origin main
```

`main`ブランチにプッシュすると、自動的にデプロイが開始されます。

#### 方法B: GitHub Actionsから手動実行

1. GitHubリポジトリの**Actions**タブを開く
2. **Deploy to Production**ワークフローを選択
3. **Run workflow**ボタンをクリック
4. **Run workflow**をクリック

## 使用方法

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
   - VPSにSSH接続
   - 最新のコードを取得
   - Docker Composeで再ビルド・再起動

### デプロイの確認

#### GitHub Actionsのログを確認

1. GitHubリポジトリの**Actions**タブを開く
2. 最新のワークフロー実行をクリック
3. ログを確認

#### VPS側で確認

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

#### プロジェクトディレクトリが見つからない

```bash
# VPS側で確認
ls -la ~/toybox
ls -la /home/app/toybox

# ディレクトリが存在しない場合は作成
mkdir -p ~/toybox
cd ~/toybox
git clone https://github.com/challenge-marlin/toybox.git .
```

#### Docker Composeエラー

```bash
# VPS側でログを確認
cd ~/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs

# コンテナの状態を確認
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps -a
```

## セキュリティ

- ✅ SSH鍵はGitHub Secretsにのみ保存（リポジトリにはコミットしない）
- ✅ `.env`ファイルは`.gitignore`に含まれている（リポジトリにはコミットしない）
- ✅ 本番環境の`.env`は手動で管理

## まとめ

これで、**ローカルで編集 → コミット → プッシュ**するだけで、本番環境に自動的に反映されます！

詳細は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) を参照してください。

