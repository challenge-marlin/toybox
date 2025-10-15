@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set COMPOSE_PROJECT_NAME=toybox
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend

