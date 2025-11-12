.PHONY: help up down restart logs shell migrate makemigrations superuser test fmt clean build collectstatic createadmin

help:
	@echo "Available commands:"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - Show logs"
	@echo "  make shell           - Open Django shell"
	@echo "  make migrate         - Run migrations"
	@echo "  make makemigrations  - Create migration files"
	@echo "  make superuser       - Create superuser"
	@echo "  make test            - Run tests"
	@echo "  make fmt             - Format code"
	@echo "  make clean           - Clean cache files"
	@echo "  make build           - Build production Docker image"
	@echo "  make collectstatic   - Collect static files"
	@echo "  make createadmin     - Create admin user (production)"

up:
	docker compose -f docker-compose.yml up -d

down:
	docker compose -f docker-compose.yml down

restart:
	docker compose -f docker-compose.yml restart

logs:
	docker compose -f docker-compose.yml logs -f

shell:
	docker compose -f docker-compose.yml exec web python manage.py shell

migrate:
	docker compose -f docker-compose.yml exec web python manage.py migrate

makemigrations:
	docker compose -f docker-compose.yml exec web python manage.py makemigrations

superuser:
	docker compose -f docker-compose.yml exec web python manage.py createsuperuser

test:
	docker compose -f docker-compose.yml exec web pytest

fmt:
	docker compose -f docker-compose.yml exec web black .
	docker compose -f docker-compose.yml exec web isort .

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build:
	docker build -f Dockerfile.prod -t toybox:latest .

collectstatic:
	docker compose -f docker-compose.yml exec web python manage.py collectstatic --noinput

createadmin:
	docker compose -f docker-compose.yml exec web python manage.py createsuperuser
