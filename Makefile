.DEFAULT_GOAL := help

.PHONY: help \
        build up down logs web-shell migrate createsuperuser runserver worker worker-logs \
        build-prod up-prod down-prod logs-prod prod-shell migrate-prod createsuperuser-prod \
        test test-all test-file test-key test-cov test-cov-html \
        lint format clean cache-clear

#################################
# HELP
#################################

help:
	@echo ""
	@echo "🚀 Доступные команды:"
	@echo ""
	@echo "  DEV:"
	@echo "    make build                 - собрать dev Docker-образы"
	@echo "    make up                    - поднять dev окружение"
	@echo "    make down                  - остановить окружение"
	@echo "    make logs                  - логи dev окружения"
	@echo "    make web-shell             - bash в dev web-контейнере"
	@echo "    make migrate               - применить миграции (dev)"
	@echo "    make createsuperuser       - создать суперпользователя (dev)"
	@echo "    make runserver             - runserver внутри dev-контейнера"
	@echo "    make worker                - запустить Celery worker (dev, доп. режим)"
	@echo "    make worker-logs           - логи Celery worker (dev)"
	@echo ""
	@echo "  PROD:"
	@echo "    make build-prod            - собрать prod-образы"
	@echo "    make up-prod               - поднять prod окружение"
	@echo "    make down-prod             - остановить prod окружение"
	@echo "    make logs-prod             - логи prod окружения"
	@echo "    make prod-shell            - bash в prod web-контейнере"
	@echo "    make migrate-prod          - применить миграции (prod)"
	@echo "    make createsuperuser-prod  - создать суперпользователя (prod)"
	@echo ""
	@echo "  TESTS:"
	@echo "    make test                  - pytest (тихий режим)"
	@echo "    make test-all              - pytest (подробно)"
	@echo "    make test-file path=...    - тест одного файла"
	@echo "    make test-key  key=...     - тесты по ключу (-k)"
	@echo "    make test-cov              - тесты с coverage (консоль)"
	@echo "    make test-cov-html         - тесты + HTML-отчёт coverage"
	@echo ""
	@echo "  LINT / FORMAT:"
	@echo "    make lint                  - ruff + isort + black (проверка)"
	@echo "    make format                - автоформатирование"
	@echo ""
	@echo "  UTILS:"
	@echo "    make clean                 - удалить *.pyc и __pycache__"
	@echo "    make cache-clear           - очистить кеш Django + pytest/ruff/coverage"
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

test-cov-html:
	docker compose exec web coverage run -m pytest
	docker compose exec web coverage html
	@echo "Откройте htmlcov/index.html для просмотра отчёта"

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

cache-clear:
	docker compose exec web python manage.py clear_cache || true
	rm -rf backend/.pytest_cache .mypy_cache .ruff_cache .coverage htmlcov || true
