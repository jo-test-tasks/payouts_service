# payouts/services.py
from decimal import Decimal

from django.db import transaction, IntegrityError

from .models import Recipient, Payout
from .validators import (
    validate_amount_positive,
    validate_currency_code,
    validate_recipient_active,
    validate_payout_status_transition,
    ensure_can_change_payout_status,
    validate_idempotency_key,
)
from .repositories import PayoutRepository


@transaction.atomic
def create_payout(
    *,
    recipient: Recipient,
    amount: Decimal,
    currency: str,
    idempotency_key: str,
) -> tuple[Payout, bool]:
    """
    Возвращает:
    - payout: объект выплаты
    - is_duplicate: True, если создавался дубль (идемпотентное повторение)
    """

    validate_amount_positive(amount)
    validate_currency_code(currency)
    validate_recipient_active(recipient)
    validate_idempotency_key(idempotency_key)

    # 1. Проверка идемпотентности
    existing = PayoutRepository.get_payout_by_idempotency_key_or_none(idempotency_key)
    if existing:
        return existing, True  # флаг: дублирование

    # 2. Создаём новую выплату
    try:
        payout = PayoutRepository.create_payout(
            recipient=recipient,
            amount=amount,
            currency=currency.upper(),
            status=Payout.Status.NEW,
            idempotency_key=idempotency_key,
        )
        return payout, False  # новая выплата
    except IntegrityError:
        # гонка: другой процесс успел создать выплату
        payout = PayoutRepository.get_payout_by_idempotency_key(idempotency_key)
        return payout, True


@transaction.atomic
def set_payout_status(
    *,
    payout: Payout,
    new_status: str,
    actor,
) -> Payout:
    ensure_can_change_payout_status(
        actor=actor,
        payout=payout,
        new_status=new_status,
    )
    validate_payout_status_transition(payout, new_status)

    updated = PayoutRepository.update_payout_status(
        payout=payout,
        new_status=new_status,
    )
    return updated
