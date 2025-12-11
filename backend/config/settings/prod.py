"""
prod.py

Продакшн-настройки.

Наследуем всё из base.py и переопределяем только то,
что должно отличаться в боевом окружении:
- DEBUG
- ALLOWED_HOSTS
- флаги безопасности (SECURE_*)
"""

import os

from .base import *  # noqa: F403

# В проде отладка всегда выключена
DEBUG = False

# ALLOWED_HOSTS берём из переменной окружения DJANGO_ALLOWED_HOSTS
# Пример в .env.prod:
# DJANGO_ALLOWED_HOSTS=my.domain.com,localhost,127.0.0.1
ALLOWED_HOSTS = (
    os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if os.getenv("DJANGO_ALLOWED_HOSTS")
    else []
)

# ==============================
# Безопасность (prod-only)
# ==============================

# В реальном проде за SSL обычно отвечает nginx/ingress.
# Здесь оставляем SECURE_SSL_REDIRECT выключенным по умолчанию,
# но даём возможность включить через окружение.
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"

# Куки только по HTTPS (когда реально есть HTTPS)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS (строгий HTTPS). В dev/staging можно временно отключить через env.
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Запрещаем встраивание сайта в iframe
X_FRAME_OPTIONS = "DENY"

# Если в проде стоишь за nginx/прокси с HTTPS → можно раскомментировать
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
