"""
dev.py

Development settings.
Overrides base.py with development-specific configuration.
"""

from .base import *  # noqa

# Enable debug mode in development
DEBUG = True

# Allow all hosts during development
ALLOWED_HOSTS = ["*"]
