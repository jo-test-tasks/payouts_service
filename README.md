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

---

## **POST `/api/payouts/`**

Create a payout (idempotent).

- Validates recipient, amount, currency, idempotency key.  
- On success:
  - returns payout DTO  
  - triggers async processing via Celery  

### **Request**
```json
{
  "recipient_id": 1,
  "amount": "100.50",
  "currency": "USD",
  "idempotency_key": "unique-key-123"
}
```

### **Response 201 Created**
```json
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

### **Response 200 (idempotent repeat)**
```json
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

---

## **GET `/api/payouts/`**

List payouts using cursor pagination.

- Results may be cached in Redis.  
- Cache automatically invalidates when payouts change.

### **Response 200**
```json
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

---

## **GET `/api/payouts/{id}/`**

Retrieve payout by ID.

### **Response 200**
```json
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

### **Response 404**
```json
{
  "detail": "Payout not found"
}
```

---

## **PATCH `/api/payouts/{id}/`**

Admin-only status update.

- Validates allowed transitions at domain level.

### **Request**
```json
{
  "status": "PROCESSING"
}
```

### **Response 200**
```json
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

### **Response 400 (invalid transition)**
```json
{
  "detail": "Invalid status transition from COMPLETED to NEW"
}
```

---

## **DELETE `/api/payouts/{id}/`**

Admin-only delete.

### **Response 204**
_No content_

### **Response 404**
```json
{
  "detail": "Payout not found"
}
```

---

## **GET `/health/`**

Service healthcheck.

### **Response 200**
```json
{
  "database": true,
  "redis": true,
  "status": "healthy"
}
```

### **Example degraded**
```json
{
  "database": false,
  "redis": true,
  "status": "degraded"
}
```


## 🧪 Tests & Coverage

Covers:

- domain logic  
- services & use cases  
- API endpoints  
- caching & cache versioning  
- Celery workflow  
- event handlers  
- healthcheck  

Run tests:

```bash
make test
```

Coverage:

```bash
make test-cov
```

---

## 🧹 Code Quality

Check:

```bash
make lint
```

Format:

```bash
make format
```

---

## ⚙️ Environments & Configuration

The project uses three settings modules:

- `config.settings.dev` — development environment  
- `config.settings.prod` — production-like environment  
- `config.settings.test` — pytest environment  

Environment files must be created based on the provided examples:

### ✔️ Development

Create `.env.dev`:

```bash
cp .env.example .env.dev
```  

### ✔️ Production

Create `.env.prod`:

```bash
cp .env.prod.example .env.prod
```

### ✔️ Tests

Pytest automatically loads:

```
DJANGO_SETTINGS_MODULE=config.settings.test
```

This environment uses:

- fast password hasher  
- local memory cache  
- Celery eager mode  
- lightweight DB configuration  

---

## ▶️ Development

Build:

```bash
make build
```

Up:

```bash
make up
```

Migrate:

```bash
make migrate
```

---

## 🚀 Production

Build:

```bash
make build-prod
```

Run:

```bash
make up-prod
```

---

## 💬 Contact

For questions or feedback — feel free to reach out.

