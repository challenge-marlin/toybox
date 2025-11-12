# PowerShell Makefile equivalent for Windows
# Usage: .\Makefile.ps1 <command>

param(
    [Parameter(Mandatory=$true)]
    [string]$Command
)

$ErrorActionPreference = "Stop"

function Invoke-DockerCompose {
    param([string[]]$Args)
    docker compose -f docker-compose.yml @Args
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
        Invoke-DockerCompose -Args @("exec", "web", "python", "manage.py", "test")
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
    "help" {
        Write-Host @"
Available commands:
  .\Makefile.ps1 up              - Start all services
  .\Makefile.ps1 down            - Stop all services
  .\Makefile.ps1 restart         - Restart all services
  .\Makefile.ps1 logs            - Show logs
  .\Makefile.ps1 shell           - Open Django shell
  .\Makefile.ps1 migrate         - Run migrations
  .\Makefile.ps1 makemigrations   - Create migrations
  .\Makefile.ps1 superuser       - Create superuser
  .\Makefile.ps1 test            - Run tests
  .\Makefile.ps1 fmt             - Format code (black, isort)
  .\Makefile.ps1 clean           - Clean pyc files
"@ -ForegroundColor Cyan
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\Makefile.ps1 help' for available commands" -ForegroundColor Yellow
        exit 1
    }
}

