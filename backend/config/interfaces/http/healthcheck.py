# config/interfaces/http/healthcheck.py
import logging

import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def healthcheck(request):
    """
    Basic healthcheck endpoint verifying DB and Redis availability.
    Returns HTTP 200 (healthy) or 503 (degraded).
    """

    db_ok = False
    redis_ok = False

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        db_ok = True
    except Exception:
        logger.exception("Healthcheck: database check failed")

    # Check Redis connectivity
    try:
        redis_client = redis.Redis.from_url(
            getattr(settings, "CELERY_BROKER_URL", "redis://redis:6379/0")
        )
        redis_client.ping()
        redis_ok = True
    except Exception:
        logger.exception("Healthcheck: redis check failed")

    status = "healthy" if db_ok and redis_ok else "degraded"
    http_status = 200 if status == "healthy" else 503

    return JsonResponse(
        {
            "database": db_ok,
            "redis": redis_ok,
            "status": status,
        },
        status=http_status,
    )
