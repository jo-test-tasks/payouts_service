"""
base.py

Базовые (общие) настройки Django-проекта.
Все окружения (dev, prod, test) будут наследоваться от этих настроек
и могут переопределять часть из них.
"""

from pathlib import Path
import os

# ==============================
# БАЗОВЫЕ ПУТИ ПРОЕКТА
# ==============================

# BASE_DIR будет указывать на папку backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Расшифровка:
# __file__                    → config/settings/base.py
# .parent                     → config/settings
# .parent                     → config
# .parent                     → backend  ← это и есть наш BASE_DIR


# ==============================
# БАЗОВЫЕ НАСТРОЙКИ
# ==============================

# В base.py мы не хардкодим секретный ключ и debug.
# Они будут переопределяться в dev/prod через переменные окружения
# и файлы dev.py/prod.py.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")

DEBUG = False  # по умолчанию выключен, включаем только в dev.py

ALLOWED_HOSTS: list[str] = []  # в dev можно оставить пустым или ['*']


# ==============================
# ПРИЛОЖЕНИЯ
# ==============================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# 2) Сторонние библиотеки (DRF, celery, django-filter и т.д.)
THIRD_PARTY_APPS = [
    "rest_framework",
    # "django_celery_results",
    # "django_celery_beat",
]

# 3) Локальные приложения проекта (наш домен)
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
# URL / WSGI
# ==============================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ==============================
# БАЗА ДАННЫХ
# ==============================

# В base.py задаём конфиг Postgres через переменные окружения.
# В dev/prod будем использовать один и тот же конфиг,
# просто значения переменных будут разными (.env.dev, .env.prod).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "payouts_dev"),
        "USER": os.getenv("POSTGRES_USER", "payouts_user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "payouts_password"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),  # имя сервиса из docker-compose
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


# ==============================
# ЯЗЫК / ВРЕМЯ / ЛОКАЛЬ
# ==============================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"  # позже можно поменять на "Europe/Kyiv", если захочешь

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
# ПАРОЛИ, ВАЛИДАТОРЫ, ТEMPLATES и т.д.
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
        "DIRS": [],  # сюда можно будет добавить глобальные шаблоны, если они появятся
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
    
    # ========= Throttling =========
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",   # для неавторизованных
        "rest_framework.throttling.UserRateThrottle",   # для авторизованных
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",    # аноним может сделать до 100 запросов в день
        "user": "1000/day",   # пользователь — до 1000 запросов в день
    },
}

# Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

# Мы игнорируем результаты — значит result backend нам НЕ нужен
CELERY_RESULT_BACKEND = None

# Чтобы Celery не пытался записывать результаты
CELERY_TASK_IGNORE_RESULT = True

# Стандартная сериализация
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"   # не обязателен, но пусть будет

CELERY_TIMEZONE = "UTC"

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_CACHE_URL", "redis://redis:6379/2"),
    }
}

