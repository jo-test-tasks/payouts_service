# Payouts Service

Небольшой сервис для управления выплатами (payouts), реализованный на Django + DRF с акцентом на:

- аккуратную доменную модель (value objects, use cases, state machine),
- идемпотентное создание выплат,
- асинхронную обработку через Celery,
- кеширование списка выплат,
- простую отказоустойчивость (fallback при падении Redis),
- прозрачное логирование и healthcheck.

Сервис можно использовать как тестовое задание и как пример архитектуры для реального backend-микросервиса.

---

## Стек

- **Python** 3.12
- **Django** 4.2
- **Django REST Framework**
- **PostgreSQL**
- **Redis**
- **Celery** (background tasks)
- **Docker / docker-compose**
- **Pytest** (unit + интеграционные тесты)

---

## Основные возможности

### Доменные фичи

- Модель выплаты (`Payout`) с привязкой к получателю (`Recipient`) и снапшотами его данных:
  - `recipient_name_snapshot`
  - `account_number_snapshot`
  - `bank_code_snapshot`
- Идемпотентное создание выплат по полю `idempotency_key`:
  - первый запрос → `201 Created`
  - повторный с тем же ключом → `200 OK` + тот же `id`
- Простейная state-machine по статусам выплаты:
  - статусы: `NEW`, `PROCESSING`, `COMPLETED`, `FAILED`
  - допустимые переходы:
    - `NEW → PROCESSING | FAILED`
    - `PROCESSING → COMPLETED | FAILED`
    - `COMPLETED` и `FAILED` — терминальные
- Валидация:
  - сумма > 0
  - валюта из списка поддерживаемых (`USD`, `EUR`, `UAH`)
  - нельзя создать выплату неактивному получателю

### API

- `GET /api/payouts/` — список выплат (курсорно-пагинированный, с кешем)
- `POST /api/payouts/` — создание выплаты (идемпотентность по `idempotency_key`)
- `GET /api/payouts/{id}/` — получение выплаты
- `PATCH /api/payouts/{id}/` — смена статуса (только `is_staff`)
- `DELETE /api/payouts/{id}/` — удаление выплаты (только `is_staff`)

Респонс списка (DRF CursorPagination):

```json
{
  "next": "http://.../api/payouts/?cursor=xxx",
  "previous": null,
  "results": [
    {
      "id": 1,
      "recipient_id": 1,
      "amount": "100.00",
      "currency": "USD",
      "status": "NEW",
      "recipient_name_snapshot": "John Doe",
      "account_number_snapshot": "UA123...",
      "bank_code_snapshot": "MFO123",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
# Payouts Service

Небольшой сервис для управления выплатами (payouts), реализованный на Django + DRF с акцентом на:

- аккуратную доменную модель (value objects, use cases, state machine),
- идемпотентное создание выплат,
- асинхронную обработку через Celery,
- кеширование списка выплат,
- простую отказоустойчивость (fallback при падении Redis),
- прозрачное логирование и healthcheck.

Сервис можно использовать как тестовое задание и как пример архитектуры для реального backend-микросервиса.

---

## Стек

- **Python** 3.12
- **Django** 4.2
- **Django REST Framework**
- **PostgreSQL**
- **Redis**
- **Celery** (background tasks)
- **Docker / docker-compose**
- **Pytest** (unit + интеграционные тесты)

---

## Основные возможности

### Доменные фичи

- Модель выплаты (`Payout`) с привязкой к получателю (`Recipient`) и снапшотами его данных:
  - `recipient_name_snapshot`
  - `account_number_snapshot`
  - `bank_code_snapshot`
- Идемпотентное создание выплат по полю `idempotency_key`:
  - первый запрос → `201 Created`
  - повторный с тем же ключом → `200 OK` + тот же `id`
- Простейная state-machine по статусам выплаты:
  - статусы: `NEW`, `PROCESSING`, `COMPLETED`, `FAILED`
  - допустимые переходы:
    - `NEW → PROCESSING | FAILED`
    - `PROCESSING → COMPLETED | FAILED`
    - `COMPLETED` и `FAILED` — терминальные
- Валидация:
  - сумма > 0
  - валюта из списка поддерживаемых (`USD`, `EUR`, `UAH`)
  - нельзя создать выплату неактивному получателю

### API

- `GET /api/payouts/` — список выплат (курсорно-пагинированный, с кешем)
- `POST /api/payouts/` — создание выплаты (идемпотентность по `idempotency_key`)
- `GET /api/payouts/{id}/` — получение выплаты
- `PATCH /api/payouts/{id}/` — смена статуса (только `is_staff`)
- `DELETE /api/payouts/{id}/` — удаление выплаты (только `is_staff`)

Респонс списка (DRF CursorPagination):

```json
{
  "next": "http://.../api/payouts/?cursor=xxx",
  "previous": null,
  "results": [
    {
      "id": 1,
      "recipient_id": 1,
      "amount": "100.00",
      "currency": "USD",
      "status": "NEW",
      "recipient_name_snapshot": "John Doe",
      "account_number_snapshot": "UA123...",
      "bank_code_snapshot": "MFO123",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
