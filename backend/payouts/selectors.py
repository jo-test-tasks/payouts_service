# payouts/selectors.py

from .models import Payout



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



