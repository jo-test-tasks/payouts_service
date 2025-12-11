# core/exceptions.py


class DomainError(Exception):
    """Базовая ошибка домена."""


class DomainValidationError(DomainError):
    """Бизнес-валидация не прошла (400)."""


class DomainNotFoundError(DomainError):
    """Сущность не найдена (404)."""


class DomainPermissionError(DomainError):
    """Нет прав на операцию (403)."""
