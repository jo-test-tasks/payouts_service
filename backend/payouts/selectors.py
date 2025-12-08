# payouts/selectors.py
from typing import Iterable

from .models import Payout
from .repositories import PayoutRepository


def list_payouts() -> Iterable[Payout]:
    """
    Базовый селектор: все выплаты, самые новые — первыми.
    Используется в GET /api/payouts/.
    """
    return (
        Payout.objects
        .select_related("recipient")
        .order_by("-created_at")
    )



