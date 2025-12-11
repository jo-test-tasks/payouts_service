.PHONY: help \
        build up down logs web-shell migrate createsuperuser runserver worker-logs worker \
        build-prod up-prod down-prod logs-prod \
        test test-all test-file test-key test-cov \
        lint format clean cache-clear

help:
	@echo ""
	@echo "🚀 Доступные команды:"
	@echo ""
	@echo "  DEV:"
	@echo "    make build             - собрать dev Docker-образы"
	@echo "    make up                - поднять dev окружение"
	@echo "    make down              - остановить dev окружение"
	@echo "    make logs              - логи dev окружения"
	@echo "    make web-shell         - зайти в контейнер web (bash)"
	@echo "    make migrate           - применить миграции"
	@echo "    make createsuperuser   - создать суперпользователя"
	@echo "    make runserver         - запустить Django runserver внутри контейнера"
	@echo "    make worker            - запустить celery worker командой внутри контейнера"
	@echo "    make worker-logs       - логи Celery worker"
	@echo ""
	@echo "  PROD:"
	@echo "    make build-prod        - собрать prod образы"
	@echo "    make up-prod           - поднять prod окружение"
	@echo "    make down-prod         - остановить prod окружение"
	@echo "    make logs-prod         - логи prod окружения"
	@echo ""
	@echo "  ТЕСТЫ:"
	@echo "    make test              - быстрый pytest"
	@echo "    make test-all          - pytest с подробным выводом"
	@echo "    make test-file path=... - прогон тестов одного файла"
	@echo "    make test-key  key=...  - тесты по ключевому слову (-k)"
	@echo "    make test-cov          - pytest с coverage отчётом"
	@echo ""
	@echo "  ЛИНТ / ФОРМАТ:"
	@echo "    make lint              - ruff + isort + black (проверка)"
	@echo "    make format            - автоформатирование ruff + isort + black"
	@echo ""
	@echo "  ПОЛЕЗНОЕ:"
	@echo "    make clean             - очистить *.pyc и __pycache__"
	@echo "    make cache-clear       - очистить Django cache + pytest/mypy/ruff cache"
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

cache-clear:
	docker compose exec web python manage.py clear_cache || true
	rm -rf backend/.pytest_cache || true
	rm -rf .mypy_cache || true
	rm -rf .ruff_cache || true
