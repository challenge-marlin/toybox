## Deployment Guide

### Prerequisites
- Docker & Docker Compose
- Environment files (copy examples and edit values):
  - `backend/env.example` -> `backend/.env` (optional but recommended)
  - `frontend/env.example` -> `frontend/.env` (optional)

### Quick Start (Docker Compose)
```bash
cd toybox-app
docker compose build
docker compose up -d
```
- Backend: `http://localhost:4000/health`
- Metrics: `http://localhost:4000/metrics`
- Frontend: `http://localhost:3000`

### Environment Variables (Backend)
- `MONGODB_URI`, `MONGODB_DB`, `PORT`
- `REDIS_URL` (BullMQ)
- `CORS_ORIGINS` (comma-separated)

### Windows Helpers
- `start-all-docker.bat`: Build & up
- `stop-all-docker.bat`: Stop & remove

### Production Notes
- Set secure `CORS_ORIGINS`
- Configure backups for MongoDB volume
- Externalize secrets (do not commit `.env`)
