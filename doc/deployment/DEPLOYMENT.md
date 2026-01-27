## Deployment Guide

### 自動デプロイ（推奨）

GitHubにプッシュするだけで自動的に本番環境にデプロイされます。

詳細は [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) を参照してください。

#### セットアップ手順

1. **VPS側でSSH鍵を生成**
2. **GitHub Secretsに鍵を登録**
3. **GitHubにプッシュ** → 自動デプロイ開始

### 手動デプロイ

#### ローカル開発環境

```bash
# 開発環境の起動
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

- Backend: `http://localhost:4000/health`
- Frontend: `http://localhost:3000`

#### 本番環境（手動）

```bash
# サーバー側で実行
cd ~/toybox
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

または、ローカルからデプロイスクリプトを実行：

```bash
./scripts/deploy.sh
```

### Prerequisites
- Docker & Docker Compose
- Environment files (copy examples and edit values):
  - `backend/env.example` -> `backend/.env` (required for production)
  - `frontend/env.example` -> `frontend/.env` (optional)

### Environment Variables (Backend)
- `MONGODB_URI`, `MONGODB_DB`, `PORT`
- `REDIS_URL` (BullMQ)
- `CORS_ORIGINS` (comma-separated)
- `JWT_SECRET` (required for production)

### Windows Helpers
- `start-all-docker.bat`: Build & up (development)
- `stop-all-docker.bat`: Stop & remove

### Production Notes
- Set secure `CORS_ORIGINS`
- Set secure `JWT_SECRET`
- Configure backups for MongoDB volume
- Externalize secrets (do not commit `.env`)
- Use automatic deployment via GitHub Actions
