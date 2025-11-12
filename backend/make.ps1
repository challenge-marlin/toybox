# PowerShell Makefile equivalent for Windows
# Usage: .\make.ps1 <command>

param(
    [Parameter(Mandatory=$false)]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Invoke-DockerCompose {
    param([string[]]$Args)
    docker compose -f docker-compose.yml @Args
}

function Build {
    Write-Host "Building production Docker image..." -ForegroundColor Green
    docker build -f Dockerfile.prod -t toybox:latest .
}

function CollectStatic {
    Write-Host "Collecting static files..." -ForegroundColor Green
    Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "collectstatic", "--noinput")
}

function CreateAdmin {
    Write-Host "Creating admin user..." -ForegroundColor Cyan
    Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "createsuperuser")
}

switch ($Command) {
    "up" {
        Write-Host "Starting all services..." -ForegroundColor Green
        Invoke-DockerCompose -Args @("up", "-d")
    }
    "down" {
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        Invoke-DockerCompose -Args @("down")
    }
    "restart" {
        Write-Host "Restarting all services..." -ForegroundColor Cyan
        Invoke-DockerCompose -Args @("restart")
    }
    "logs" {
        Write-Host "Showing logs..." -ForegroundColor Magenta
        Invoke-DockerCompose -Args @("logs", "-f")
    }
    "shell" {
        Write-Host "Opening Django shell..." -ForegroundColor Cyan
        Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "shell")
    }
    "migrate" {
        Write-Host "Running migrations..." -ForegroundColor Green
        Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "migrate")
    }
    "makemigrations" {
        Write-Host "Creating migrations..." -ForegroundColor Green
        Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "makemigrations")
    }
    "superuser" {
        Write-Host "Creating superuser..." -ForegroundColor Cyan
        Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "createsuperuser")
    }
    "test" {
        Write-Host "Running tests..." -ForegroundColor Yellow
        Invoke-DockerCompose -Args @("exec", "web", "pytest")
    }
    "fmt" {
        Write-Host "Formatting code..." -ForegroundColor Magenta
        Write-Host "Note: black and isort need to be installed in the container" -ForegroundColor Yellow
        Invoke-DockerCompose -Args @("exec", "web", "black", ".")
        Invoke-DockerCompose -Args @("exec", "web", "isort", ".")
    }
    "clean" {
        Write-Host "Cleaning Python cache files..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Include *.pyc -Recurse -Force | Remove-Item -Force
        Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse
    }
    "build" {
        Build
    }
    "collectstatic" {
        CollectStatic
    }
    "createadmin" {
        CreateAdmin
    }
    "help" {
        Write-Host @"
Available commands:
  .\make.ps1 up              - Start all services
  .\make.ps1 down            - Stop all services
  .\make.ps1 restart         - Restart all services
  .\make.ps1 logs            - Show logs
  .\make.ps1 shell           - Open Django shell
  .\make.ps1 migrate         - Run migrations
  .\make.ps1 makemigrations  - Create migrations
  .\make.ps1 superuser       - Create superuser
  .\make.ps1 test            - Run tests
  .\make.ps1 fmt             - Format code (black, isort)
  .\make.ps1 clean           - Clean pyc files
  .\make.ps1 build           - Build production Docker image
  .\make.ps1 collectstatic   - Collect static files
  .\make.ps1 createadmin     - Create admin user
"@ -ForegroundColor Cyan
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\make.ps1 help' for available commands" -ForegroundColor Yellow
        exit 1
    }
}
