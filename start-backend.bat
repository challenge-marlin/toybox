@echo off
setlocal
cd /d %~dp0backend
echo Starting ToyBox Backend...
node -v
echo PORT=%PORT% MONGODB_URI=%MONGODB_URI% REDIS_URL=%REDIS_URL%
npm run dev

