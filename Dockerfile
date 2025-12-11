# Dockerfile (Production)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# System dependencies required for psycopg2 and other C-based packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install runtime dependencies only
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend /app/backend

WORKDIR /app/backend

# Expose application port (optional but useful for clarity)
EXPOSE 8000

# Use Gunicorn in production
# All environment variables (including DJANGO_SETTINGS_MODULE) come from .env.prod
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
