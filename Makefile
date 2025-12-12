.DEFAULT_GOAL := help

.PHONY: help \
        build up down logs web-shell runserver migrate createsuperuser worker worker-logs \
        build-prod up-prod down-prod logs-prod prod-shell migrate-prod createsuperuser-prod \
        test test-all test-file test-key test-cov \
        lint format clean

#################################
# HELP
#################################

help:
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "DEV:"
	@echo "  make build               - build dev Docker images"
	@echo "  make up                  - start dev environment"
	@echo "  make down                - stop dev environment"
	@echo "  make logs                - tail dev logs"
	@echo "  make web-shell           - open bash inside dev web container"
	@echo "  make runserver           - run Django dev server"
	@echo "  make migrate             - apply migrations (dev)"
	@echo "  make createsuperuser     - create Django superuser (dev)"
	@echo "  make worker              - start Celery worker (dev)"
	@echo "  make worker-logs         - tail Celery worker logs (dev)"
	@echo ""
	@echo "PROD:"
	@echo "  make build-prod          - build production images"
	@echo "  make up-prod             - start production environment"
	@echo "  make down-prod           - stop production environment"
	@echo "  make logs-prod           - tail production logs"
	@echo "  make prod-shell          - open bash inside prod web container"
	@echo "  make migrate-prod        - apply migrations (prod)"
	@echo "  make createsuperuser-prod- create Django superuser (prod)"
	@echo ""
	@echo "TESTS:"
	@echo "  make test                - run pytest (quiet)"
	@echo "  make test-all            - run pytest (verbose)"
	@echo "  make test-file path=...  - run tests for a specific file"
	@echo "  make test-key key=...    - run tests by keyword (-k)"
	@echo "  make test-cov            - run tests with coverage"
	@echo ""
	@echo "LINT / FORMAT:"
	@echo "  make lint                - ruff + isort + black (check)"
	@echo "  make format              - auto-format codebase"
	@echo ""
	@echo "UTILS:"
	@echo "  make clean               - remove *.pyc and __pycache__"
	@echo ""

#################################
# DEV
#################################

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

web-shell:
	docker compose exec web bash

runserver:
	docker compose exec web python manage.py runserver 0.0.0.0:8000

migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

worker:
	docker compose exec worker celery -A config worker -l info

worker-logs:
	docker compose logs -f worker

#################################
# PROD
#################################

build-prod:
	docker compose -f docker-compose.prod.yml build

up-prod:
	docker compose -f docker-compose.prod.yml up -d

down-prod:
	docker compose -f docker-compose.prod.yml down

logs-prod:
	docker compose -f docker-compose.prod.yml logs -f

prod-shell:
	docker compose -f docker-compose.prod.yml exec web bash

migrate-prod:
	docker compose -f docker-compose.prod.yml exec web python manage.py migrate

createsuperuser-prod:
	docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

#################################
# TESTS
#################################

test:
	docker compose exec web pytest -q

test-all:
	docker compose exec web pytest -vv

test-file:
	docker compose exec web pytest -vv $(path)

test-key:
	docker compose exec web pytest -vv -k "$(key)"

test-cov:
	docker compose exec web coverage run -m pytest
	docker compose exec web coverage report -m

#################################
# LINT / FORMAT
#################################

lint:
	docker compose exec web ruff check .
	docker compose exec web isort . --check-only
	docker compose exec web black . --check

format:
	docker compose exec web ruff format .
	docker compose exec web isort .
	docker compose exec web black .

#################################
# UTILS
#################################

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
