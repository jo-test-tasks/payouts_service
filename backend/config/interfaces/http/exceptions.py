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
    """
    Custom exception handler that maps domain-level errors
    to appropriate HTTP responses.
    """

    # Let DRF handle built-in exceptions first
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # Domain validation error → 400
    if isinstance(exc, DomainValidationError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Domain object not found → 404
    if isinstance(exc, DomainNotFoundError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Permission denied → 403
    if isinstance(exc, DomainPermissionError):
        return Response(
            {"detail": str(exc)},
            status=status.HTTP_403_FORBIDDEN,
        )

    # All other unhandled errors → 500
    return Response(
        {"detail": "Internal server error."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
