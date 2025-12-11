import os

from celery import Celery

# Берём настройки Django из окружения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")

# Подтягиваем все настройки, начинающиеся с CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически искать tasks.py в указанных модулях
app.autodiscover_tasks(
    [
        "infrastructure.payouts",  # наши инфра-таски для payouts
        # если захочешь, позже добавишь ещё домены/инфру
    ]
)
