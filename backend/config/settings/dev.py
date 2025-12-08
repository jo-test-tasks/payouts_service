"""
dev.py

Настройки для локальной разработки.
Наследуемся от base.py и переопределяем то, что нужно для dev.
"""

from .base import *  # noqa

# В dev включаем DEBUG и разрешаем доступ со всех хостов.
DEBUG = True

ALLOWED_HOSTS = ["*"]
