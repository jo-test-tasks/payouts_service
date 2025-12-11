"""
base.py

Base Django settings shared across all environments (dev, prod, test).
Environment-specific settings override these defaults in dev.py / prod.py / test.py.
"""

import os
from pathlib import Path

# ==============================
# PATHS
# ==============================

# BASE_DIR points to the backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ==============================
# CORE SETTINGS
# ==============================

# Secret key is provided via environment (see dev/prod env files)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")

# Debug is disabled by default and explicitly enabled only in dev.py
DEBUG = False

# Will be overridden in dev/prod settings if needed
ALLOWED_HOSTS: list[str] = []


# ==============================
# APPLICATIONS
# ==============================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    # "django_celery_results",
    # "django_celery_beat",
]

LOCAL_APPS = [
    "payouts.apps.PayoutsConfig",
    # "core",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ==============================
# MIDDLEWARE
# ==============================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==============================
# URL / WSGI / ASGI
# ==============================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ==============================
# DATABASE
# ==============================

# PostgreSQL configuration is driven by environment variables.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "payouts_dev"),
        "USER": os.getenv("POSTGRES_USER", "payouts_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "payouts_password"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),  # service name from docker-compose
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


# ==============================
# I18N / TIMEZONE
# ==============================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True
USE_TZ = True


# ==============================
# STATIC / MEDIA
# ==============================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ==============================
# AUTH / PASSWORDS / TEMPLATES
# ==============================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Global template dirs can be added here if needed
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==============================
# DEFAULT PRIMARY KEY
# ==============================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==============================
# DRF
# ==============================

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "EXCEPTION_HANDLER": "config.interfaces.http.exceptions.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },
}


# ==============================
# CELERY
# ==============================

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

# We ignore task results, so no result backend is configured
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True

CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_REJECT_ON_WORKER_LOST = True

CELERY_TASK_TIME_LIMIT = 30
CELERY_TASK_SOFT_TIME_LIMIT = 20

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Standard JSON-based serialization
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"


# ==============================
# DATABASE CONNECTION LIFETIME
# ==============================

DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DB_CONN_MAX_AGE", "60"))


# ==============================
# CACHE
# ==============================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_CACHE_URL", "redis://redis:6379/2"),
    }
}


# ==============================
# LOGGING
# ==============================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", LOG_LEVEL),
            "propagate": False,
        },
        "payouts": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "infrastructure.payouts": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
