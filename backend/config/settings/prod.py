"""
prod.py

Продакшн-настройки.
В реальном проде здесь должны быть:
- DEBUG = False
- корректный ALLOWED_HOSTS
- настройки безопасности, логирования, кэшей и т.д.
"""

from .base import *  # noqa: F403
import os

DEBUG = False

# В проде не оставляем пустым.
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if os.getenv("DJANGO_ALLOWED_HOSTS") else []
