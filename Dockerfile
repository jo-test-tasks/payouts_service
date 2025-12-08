# Dockerfile (PROD)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Только runtime-зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Кладём backend внутрь образа
COPY backend /app/backend

WORKDIR /app/backend

# Для тестового можно оставить runserver.
# В реальном проде тут обычно gunicorn/uvicorn.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
