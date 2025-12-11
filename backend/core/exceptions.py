# core/exceptions.py


class DomainError(Exception):
    """Base class for all domain-level errors."""


class DomainValidationError(DomainError):
    """Domain validation failed (HTTP 400)."""


class DomainNotFoundError(DomainError):
    """Domain entity not found (HTTP 404)."""


class DomainPermissionError(DomainError):
    """Operation not permitted (HTTP 403)."""
