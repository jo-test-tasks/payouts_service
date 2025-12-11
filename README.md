# Payouts Service
Made with ❤️ by Evhen

A production-grade payout processing backend built with **Django**, **DRF**, **Celery**, **Redis**, and **PostgreSQL**.  
Designed using **Clean Architecture** and **DDD principles** to keep business logic isolated, infrastructure interchangeable, and the system maintainable and extensible.

## TL;DR

- Django + DRF + Celery + Redis + PostgreSQL  
- Clean Architecture + DDD-inspired layering  
- Idempotent payout creation with race-condition handling  
- Event-driven async payout processing via Celery  
- Redis-backed payout list cache with versioned invalidation  
- High test coverage (~95–100%)  
- Fully dockerized dev/prod environments  
- Makefile automation for tests, linting, and running the stack

---

## 🧩 About This Project (Test Assignment)

This project was implemented as a **technical test assignment**.

The goal was not only to satisfy the functional requirements, but to demonstrate:

- a mature backend service structure,  
- production-ready patterns,  
- isolation of domain logic,  
- async workflows,  
- idempotent operations,  
- and strong test coverage.

Even though the business scope is small, the architecture mirrors real-world financial systems.

---

## 🔧 Tech Stack

| Component              | Usage                      |
|------------------------|----------------------------|
| **Django 4.2 LTS**     | Core framework             |
| **Django REST Framework** | API layer              |
| **Celery**             | Background processing      |
| **Redis**              | Message broker + cache     |
| **PostgreSQL**         | Primary database           |
| **Docker / Docker Compose** | Environment         |
| **Gunicorn**           | Production WSGI server     |
| **Pytest**             | Test suite                 |
| **Ruff / Black / isort** | Code quality & style    |
| **coverage.py**        | Test coverage reports      |

---

## 📁 Project Structure

```text
.
├── docker-compose.yml           # Dev environment (Django dev server)
├── docker-compose.prod.yml      # Prod-like environment (Gunicorn + Celery)
├── Dockerfile                   # Production image
├── Dockerfile.dev               # Development image
├── Makefile                     # Dev/prod/test automation
├── requirements.txt
├── requirements.dev.txt
├── README.md
│
└── backend
    ├── config
    │   ├── settings/
    │   │   ├── base.py          # Shared settings
    │   │   ├── dev.py           # Dev overrides
    │   │   ├── prod.py          # Prod overrides
    │   │   └── test.py          # Test overrides
    │   ├── interfaces/http/     # HTTP-level concerns (exceptions, healthcheck)
    │   ├── celery.py
    │   ├── urls.py
    │   ├── asgi.py / wsgi.py
    │   └── __init__.py
    │
    ├── core
    │   ├── event_bus.py         # Simple event bus abstraction
    │   ├── exceptions.py
    │   └── __init__.py
    │
    ├── payouts
    │   ├── api/                 # DRF API views & serializers
    │   ├── application/         # Use cases (application services)
    │   ├── domain/              # Value objects, validators, domain services
    │   ├── events.py            # Domain events
    │   ├── pagination.py        # Cursor-based pagination
    │   ├── repositories.py      # Repository abstractions
    │   ├── selectors.py         # Read model helpers
    │   ├── models.py            # Django ORM models
    │   ├── apps.py / admin.py
    │   └── migrations/
    │
    ├── infrastructure
    │   └── payouts
    │       ├── cache.py         # Redis cache helpers + versioning
    │       ├── event_handlers.py# Wiring domain events to Celery
    │       ├── tasks.py         # Celery tasks (async workflow)
    │       └── __init__.py
    │
    └── tests
        ├── payouts/             # Domain, services, API, use case tests
        ├── infrastructure/      # Cache, Celery, event handlers
        ├── test_healthcheck.py  # /health endpoint
        └── __init__.py
```

---

## 🧠 Domain & Architecture Overview

### Clean Architecture Layers

```text
┌───────────────────────────┐
│        Interfaces         │  ← DRF API, serializers, HTTP exceptions
└────────────┬──────────────┘
             │
┌────────────▼──────────────┐
│        Application        │  ← Use cases coordinate workflows,
│                            │     trigger domain events, call repos
└────────────┬──────────────┘
             │
┌────────────▼──────────────┐
│          Domain           │  ← Pure business logic, value objects,
│                            │     invariants, state transitions
└────────────┬──────────────┘
             │
┌────────────▼──────────────┐
│       Infrastructure      │  ← Celery, cache, DB, event handlers,
│                            │     Django ORM implementations
└───────────────────────────┘
```

### Domain Concepts

**Entities**

- `Recipient`
- `Payout`

**Value Objects**

- `Money`
- `IdempotencyKey`
- `PayoutStatus` (enum-like status type)

**Rules**

- Status transitions strictly controlled at the domain level.  
- Inactive recipients cannot receive payouts.  
- Staff-only operations (status change, delete) guarded at application/API layer.  

---

## 🪄 Event-Driven Flow

1. Client calls **`POST /api/payouts/`**.
2. Application layer creates a `Payout` entity and raises a domain event.
3. Event handlers publish tasks to Celery.
4. Celery tasks:
   - move payout through states: **NEW → PROCESSING → COMPLETED**
   - bump payouts list cache version in Redis
   - trigger lazy cache rebuild when needed.

```text
Create payout
      ↓
Publish domain event (PayoutCreated)
      ↓
Event handlers trigger Celery tasks
      ↓
Async status transition NEW → PROCESSING → COMPLETED
      ↓
Cache version bump → payouts list cache invalidation
```

All write paths are idempotent and safe to retry.

---

## 🧊 Caching & Pagination

### Redis Caching With Versioning

- Payout list responses are cached in Redis.
- A dedicated *cache version key* is incremented on each write (create/update/delete).
- Cache keys include the current version, so old values are invalidated automatically.

This makes cache invalidation explicit and predictable.

### Cursor-Based Pagination

- List endpoint uses **cursor-based pagination** rather than offset/limit.
- More robust for large tables and concurrent inserts.

---

## 📘 API Overview

### **POST `/api/payouts/`**

Create a payout (idempotent).

- Validates recipient, amount, currency, idempotency key.
- On success:
  - returns payout DTO
  - triggers async processing via Celery.

```
Request:

json
{
  "recipient_id": 1,
  "amount": "100.50",
  "currency": "USD",
  "idempotency_key": "unique-key-123"
}
```

```
Response 201 Created:

json
{
  "id": 10,
  "recipient_id": 1,
  "amount": "100.50",
  "currency": "USD",
  "status": "NEW",
  "recipient_name_snapshot": "John Doe",
  "account_number_snapshot": "UA1234567890",
  "bank_code_snapshot": "MFO123",
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

```Response 200 (Idempotent repeat):

json
{
  "id": 10,
  "recipient_id": 1,
  "amount": "100.50",
  "currency": "USD",
  "status": "NEW",
  "recipient_name_snapshot": "John Doe",
  "account_number_snapshot": "UA1234567890",
  "bank_code_snapshot": "MFO123",
  "created_at": "...",
  "updated_at": "..."
}
```
### **GET `/api/payouts/`**

List payouts with cursor pagination.

- Results are cached in Redis.
- Cache invalidates automatically when payouts change.

```Response 200:

json
{
  "next": "http://localhost:8000/api/payouts/?cursor=cD0y",
  "previous": null,
  "results": [
    {
      "id": 12,
      "recipient_id": 1,
      "amount": "150.00",
      "currency": "USD",
      "status": "PROCESSING",
      "recipient_name_snapshot": "John Doe",
      "account_number_snapshot": "UA123...",
      "bank_code_snapshot": "MFO123",
      "created_at": "2025-01-01T12:30:00Z",
      "updated_at": "2025-01-01T12:31:00Z"
    },
    {
      "id": 11,
      "recipient_id": 1,
      "amount": "100.00",
      "currency": "USD",
      "status": "NEW",
      "recipient_name_snapshot": "John Doe",
      "account_number_snapshot": "UA123...",
      "bank_code_snapshot": "MFO123",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ]
}
```
### **GET `/api/payouts/{id}/`**

Retrieve single payout by ID.

```Response 200
{
  "id": 10,
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
```
```Response 400
{
  "detail": "Payout not found"
}
```
### **PATCH `/api/payouts/{id}/`**

Admin-only status change.

- Validates allowed transitions at domain level.

```Request:
{
  "status": "PROCESSING"
}
```

```Response 200
{
  "id": 10,
  "recipient_id": 1,
  "amount": "100.00",
  "currency": "USD",
  "status": "PROCESSING",
  "recipient_name_snapshot": "John Doe",
  "account_number_snapshot": "UA123...",
  "bank_code_snapshot": "MFO123",
  "created_at": "...",
  "updated_at": "..."
}
```

```Response 400 (Invalid transition)

{
  "detail": "Invalid status transition from COMPLETED to NEW"
}s
```
### **DELETE `/api/payouts/{id}/`**

Admin-only delete.
```Response 204

(no content)
```

```Response 404
{
  "detail": "Payout not found"
}
```
### **GET `/health/`**

Simple healthcheck endpoint, covered by tests.
```Response 200
{
  "database": true,
  "redis": true,
  "status": "healthy"
}
```

```Example degraded:
{
  "database": false,
  "redis": true,
  "status": "degraded"
}
```
---

## 🧪 Tests & Coverage

Tests are implemented with **pytest** and **pytest-django** and cover:

- domain value objects and validators  
- services and use cases  
- API endpoints (happy path + negative scenarios)  
- cache behavior and versioning  
- Celery tasks and event handlers  
- healthcheck endpoint  

Test settings (`config.settings.test`) configure:

- fast password hasher  
- in-memory email backend  
- local-memory cache backend  
- Celery in **eager mode** (`CELERY_TASK_ALWAYS_EAGER=True`), so tests do not depend on a running worker.

Typical line coverage is around **95–100%** for the core payouts domain and infrastructure.

### Run tests (quiet):

```bash
make test
```

### Run tests (verbose):

```bash
make test-all
```

### Run single file:

```bash
make test-file path=backend/tests/payouts/test_api_payouts.py
```

### Filter tests by keyword:

```bash
make test-key key=payouts
```

### Coverage (console):

```bash
make test-cov
```

### Coverage (HTML report):

```bash
make test-cov-html
# open htmlcov/index.html in browser
```

---

## 🧹 Code Quality (Lint & Format)

Static analysis and formatting are enforced via **Ruff**, **isort**, and **Black**.

### Check only (CI-style):

```bash
make lint
# runs:
#   ruff check .
#   isort . --check-only
#   black . --check
```

### Auto-fix / auto-format:

```bash
make format
# runs:
#   ruff format .
#   isort .
#   black .
```

---

## ⚙️ Environments & Configuration

Project uses three settings modules:

- `config.settings.dev` — local development  
- `config.settings.prod` — production‑like environment  
- `config.settings.test` — pytest configuration  

You must create two files based on examples:

### ✔️ `.env.dev` — for development

Create file:

```
cp .env.example .env.dev
```

Minimal content:

```
# ===========================
# Django
# ===========================

# Django settings module
DJANGO_SETTINGS_MODULE=config.settings.dev

# Development secret key (NOT for production)
DJANGO_SECRET_KEY=dev-secret-key-change-me

# Debug mode: 1 = True, 0 = False
DJANGO_DEBUG=1

# Allowed hosts for local development
ALLOWED_HOSTS=*


# ===========================
# PostgreSQL
# ===========================

# Must match docker-compose.yml values
POSTGRES_DB=payouts_dev
POSTGRES_USER=payouts_user
POSTGRES_PASSWORD=payouts_password
POSTGRES_HOST=db
POSTGRES_PORT=5432


# ===========================
# Redis / Celery
# ===========================

# Redis broker for Celery
CELERY_BROKER_URL=redis://redis:6379/0

# Redis instance for Django cache
REDIS_CACHE_URL=redis://redis:6379/2

# Optional general-purpose Redis URL
REDIS_URL=redis://redis:6379/0


# ===========================
# Misc
# ===========================

# Logging level (INFO / DEBUG / WARNING / ERROR)
LOG_LEVEL=INFO

# Database connection max lifetime (seconds)
DB_CONN_MAX_AGE=60

```

---

### ✔️ `.env.prod` — for production

Create:

```
cp .env.prod.example .env.prod
```

Content:

```
# ===========================
# Django (Production)
# ===========================

DJANGO_SETTINGS_MODULE=config.settings.prod

# Strong, random secret key (must be replaced in production)
DJANGO_SECRET_KEY=!!!_REPLACE_WITH_SECURE_SECRET_KEY_!!!

# Debug must remain disabled in production
DJANGO_DEBUG=0

# Allowed hosts for production environment
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Logging level
LOG_LEVEL=INFO

# Database connection max lifetime (seconds)
DB_CONN_MAX_AGE=60


# ===========================
# PostgreSQL (Production)
# ===========================

POSTGRES_DB=payouts_prod
POSTGRES_USER=payouts_user
POSTGRES_PASSWORD=!!!_REPLACE_WITH_SECURE_PASSWORD_!!!
POSTGRES_HOST=db
POSTGRES_PORT=5432


# ===========================
# Redis / Celery (Production)
# ===========================

# General-purpose Redis URL
REDIS_URL=redis://redis:6379/0

# Celery broker
CELERY_BROKER_URL=redis://redis:6379/0

# Redis instance for Django cache
REDIS_CACHE_URL=redis://redis:6379/2
```

---

## ▶️ Running in Development

### 0. Prerequisites

- Docker & Docker Compose
- `make`

### 1. Build dev images

```bash
make build
```

### 2. Start dev environment

```bash
make up
```

This will start:

- `web` – Django dev server (`runserver`)
- `db` – PostgreSQL
- `redis` – Redis
- `worker` – Celery worker (runs in background as a separate service)

### 3. Apply migrations

```bash
make migrate
```

### 4. Create superuser (optional)

```bash
make createsuperuser
```

### 5. Useful dev commands

```bash
make logs         # follow all dev logs
make web-shell    # bash shell inside web container
make worker-logs  # follow Celery worker logs
make runserver    # run Django dev server manually (if needed)
```

Application will be available at:

- API: `http://localhost:8000/api/payouts/`
- Admin: `http://localhost:8000/admin/`
- Healthcheck: `http://localhost:8000/health/`

---

## 🚀 Running in Production (Docker Compose)

The `docker-compose.prod.yml` file starts a **Gunicorn-based** Django app and a Celery worker, using separate volumes for PostgreSQL and Redis.

### 1. Build production images

```bash
make build-prod
```

### 2. Start production stack

```bash
make up-prod
```

This starts:

- `payouts_web`    – Gunicorn serving Django (`config.wsgi:application`)
- `payouts_worker` – Celery worker
- `payouts_db`     – PostgreSQL (prod DB)
- `payouts_redis`  – Redis

### 3. Run migrations in prod

```bash
make migrate-prod
```

### 4. Create superuser in prod

```bash
make createsuperuser-prod
```

### 5. Useful prod commands

```bash
make logs-prod    # follow prod logs
make down-prod    # stop prod stack
make prod-shell   # bash shell inside prod web container
```

By default, Gunicorn listens on:

```text
http://0.0.0.0:8000
```

In a real deployment, this would typically sit behind a reverse proxy such as Nginx.

---

## 🔧 Maintenance & Utilities

### Clean Python artifacts

```bash
make clean
# removes *.pyc and __pycache__ folders
```

### Clear caches (Django, pytest, ruff, coverage)

```bash
make cache-clear
# runs Django clear_cache and removes local cache dirs
```

---

## 🧹 Code Quality & Structure

The codebase is structured for:

- clear separation of domain and infrastructure  
- minimal framework leakage into the domain layer  
- testability of each layer in isolation  
- explicit event-driven flows instead of hidden side effects  

The combination of:

- DDD-inspired structure  
- Celery-based async workflow  
- Redis caching with versioning  
- high test coverage  
- Dockerized dev/prod setups  

makes this service a compact but realistic example of how a real-world payout processing backend can be designed.

---

## 💬 Contact

For questions or feedback, feel free to reach out.
