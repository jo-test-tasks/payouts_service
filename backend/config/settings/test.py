from .base import *  # noqa: F403

# Debug disabled for test environment
DEBUG = False

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# In-memory email backend for test isolation
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery executed synchronously during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# In-memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405

# Minimal logging configuration for test environment
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}
