# Dockerfile (PROD)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Ставим системные зависимости (для psycopg2 / других C-зависимостей)
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

# Открываем порт для приложения (опционально, но красиво)
EXPOSE 8000

# В реальном проде используем gunicorn, а не runserver
# DJANGO_SETTINGS_MODULE и прочие берём из .env.prod
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
# Dockerfile (PROD)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Ставим системные зависимости (для psycopg2 / других C-зависимостей)
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

# Открываем порт для приложения (опционально, но красиво)
EXPOSE 8000

# В реальном проде используем gunicorn, а не runserver
# DJANGO_SETTINGS_MODULE и прочие берём из .env.prod
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
