# config/interfaces/http/healthcheck.py
import logging

from django.http import JsonResponse
from django.db import connection
from django.conf import settings

import redis

logger = logging.getLogger(__name__)


def healthcheck(request):
    db_ok = False
    redis_ok = False

    # DB check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        db_ok = True
    except Exception:
        logger.exception("Healthcheck: database check failed")

    # Redis check
    try:
        r = redis.Redis.from_url(getattr(settings, "CELERY_BROKER_URL", "redis://redis:6379/0"))
        r.ping()
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
