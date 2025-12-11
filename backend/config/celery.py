import os

from celery import Celery

# Load Django settings from environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")

# Load all CELERY_* settings from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks modules
app.autodiscover_tasks(
    [
        "infrastructure.payouts",  # infrastructure-level tasks for payouts domain
        # Additional modules can be added here
    ]
)
