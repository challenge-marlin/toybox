@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d %~dp0
set COMPOSE_PROJECT_NAME=toybox

if /I "%~1"=="build" (
  docker compose build || goto :eof
)

docker compose up -d

