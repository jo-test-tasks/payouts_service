# config/api/exceptions.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions import (
    DomainNotFoundError,
    DomainPermissionError,
    DomainValidationError,
)


def custom_exception_handler(exc, context):
    # Сначала пусть DRF попробует обработать свои стандартные ошибки
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # Доменная валидация → 400
    if isinstance(exc, DomainValidationError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Не найдено → 404
    if isinstance(exc, DomainNotFoundError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Нет прав → 403
    if isinstance(exc, DomainPermissionError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Всё остальное — 500
    return Response(
        {"detail": "Internal server error."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
