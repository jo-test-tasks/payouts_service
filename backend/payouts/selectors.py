# payouts/selectors.py
from typing import Iterable

from .models import Payout
from .repositories import PayoutRepository


def list_payouts():
    """
    Базовый селектор для списка выплат.
    Возвращаем queryset с детерминированным порядком.
    """
    return (
        Payout.objects
        .select_related("recipient")
        .order_by("-created_at", "-id")  # стабильный порядок для курсора
    )



