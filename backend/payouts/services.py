# payouts/services.py
from decimal import Decimal
from django.db import transaction

from .models import Recipient, Payout
from .validators import (
    validate_amount_positive,
    validate_currency_code,
    validate_recipient_active,
    validate_payout_status_transition,
    ensure_can_change_payout_status,
)


@transaction.atomic
def create_payout(*, recipient: Recipient, amount: Decimal, currency: str) -> Payout:
    # ДОМЕННАЯ ВАЛИДАЦИЯ
    validate_amount_positive(amount)
    validate_currency_code(currency)
    validate_recipient_active(recipient)

    payout = Payout(
        recipient=recipient,
        amount=amount,
        currency=currency.upper(),
        status=Payout.Status.NEW,
    )
    payout.fill_recipient_snapshot()
    payout.save()
    return payout




@transaction.atomic
def set_payout_status(
    *,
    payout: Payout,
    new_status: str,
    actor,   # ← НОВЫЙ параметр: кто пытается сменить статус
) -> Payout:
    # 1. Проверка прав
    ensure_can_change_payout_status(actor=actor, payout=payout, new_status=new_status)

    # 2. Проверка допустимости перехода (state machine)
    validate_payout_status_transition(payout, new_status)

    # 3. Применяем изменение
    payout.status = new_status
    payout.save(update_fields=["status", "updated_at"])
    return payout