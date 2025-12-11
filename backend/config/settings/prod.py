"""
prod.py

Production settings.
Inherits from base.py and overrides production-specific configuration:
- DEBUG
- ALLOWED_HOSTS
- security-related flags (SECURE_*)
"""

import os

from .base import *  # noqa: F403

# Debug must always remain disabled in production
DEBUG = False


# Allowed hosts are provided via DJANGO_ALLOWED_HOSTS (comma-separated)
ALLOWED_HOSTS = (
    os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if os.getenv("DJANGO_ALLOWED_HOSTS")
    else []
)


# ==============================
# SECURITY (production-only)
# ==============================

# SSL redirection (usually handled by reverse proxy; enabled via env if needed)
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "0") == "1"

# Cookies served only via HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Prevent embedding in iframes
X_FRAME_OPTIONS = "DENY"

# If the app is running behind an HTTPS reverse proxy (nginx, ingress)
# you may enable this:
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
