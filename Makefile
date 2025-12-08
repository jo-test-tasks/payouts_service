.PHONY: help build build-prod up up-prod down down-prod logs logs-prod \
        web-shell migrate createsuperuser worker-logs \
        test test-all test-file test-key test-cov \
        lint format

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "  DEV:"
	@echo "    make build           - собрать dev Docker-образы"
	@echo "    make up              - поднять dev окружение"
	@echo "    make down            - остановить dev окружение"
	@echo "    make logs            - логи dev окружения"
	@echo "    make web-shell       - зайти в контейнер web (dev)"
	@echo "    make migrate         - миграции (dev)"
	@echo "    make createsuperuser - создать суперпользователя (dev)"
	@echo "    make worker-logs     - логи Celery worker (dev)"
	@echo ""
	@echo "  PROD:"
	@echo "    make build-prod      - собрать prod Docker-образы"
	@echo "    make up-prod         - поднять prod окружение"
	@echo "    make down-prod       - остановить prod окружение"
	@echo "    make logs-prod       - логи prod окружения"
	@echo ""
	@echo "  ТЕСТЫ:"
	@echo "    make test            - быстрый запуск pytest внутри dev-контейнера"
	@echo "    make test-all        - запуск всех тестов с подробным выводом"
	@echo "    make test-file path=... - тесты только одного файла"
	@echo "    make test-key  key=...  - тесты по ключевому слову (-k)"
	@echo "    make test-cov         - pytest с coverage-отчётом"
	@echo ""
	@echo "  ЛИНТ / ФОРМАТИРОВАНИЕ:"
	@echo "    make lint            - проверка ruff + isort + black (без изменений)"
	@echo "    make format          - автоформатирование ruff format + isort + black"

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

migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

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
# ТЕСТЫ (dev container)
#################################

# Быстрый прогон всех тестов (тихий режим)
test:
	docker compose exec web pytest -q

# Подробный прогон всех тестов
test-all:
	docker compose exec web pytest -vv

# Прогон тестов для одного файла:
#   make test-file path=backend/tests/payouts/test_services_payouts.py
test-file:
	docker compose exec web pytest -vv $(path)

# Прогон тестов по ключевому слову:
#   make test-key key=validators
test-key:
	docker compose exec web pytest -vv -k "$(key)"

# Покрытие кода
test-cov:
	docker compose exec web coverage run -m pytest
	docker compose exec web coverage report -m

#################################
# ЛИНТ / ФОРМАТ (dev container)
#################################

# Проверка, что код отформатирован и без ошибок стиля
lint:
	docker compose exec web ruff check .
	docker compose exec web isort . --check-only
	docker compose exec web black . --check

# Автоформатирование кода
format:
	docker compose exec web ruff format .
	docker compose exec web isort .
	docker compose exec web black .
