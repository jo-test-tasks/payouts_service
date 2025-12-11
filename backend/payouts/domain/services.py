# payouts/domain/services.py
from payouts.domain.validators import (
    ensure_can_change_payout_status,
    validate_payout_status_transition,
    validate_recipient_active,
)
from payouts.domain.value_objects import IdempotencyKey, Money, PayoutStatus
from payouts.models import Payout, Recipient


def build_money(amount, currency) -> Money:
    return Money(amount=amount, currency=currency)


def build_idempotency_key(value) -> IdempotencyKey:
    return IdempotencyKey(value)


def build_payout_status(value: str) -> PayoutStatus:
    return PayoutStatus(value=value)


def build_new_payout(
    *,
    recipient: Recipient,
    money: Money,
    key: IdempotencyKey,
) -> Payout:
    validate_recipient_active(recipient)

    payout = Payout(
        recipient=recipient,
        amount=money.amount,
        currency=money.currency,
        status=Payout.Status.NEW,
        idempotency_key=key.value,
    )
    payout.fill_recipient_snapshot()
    return payout


def change_status(payout: Payout, new_status: PayoutStatus, *, actor) -> Payout:
    """
    Доменный переход статуса:
    - права
    - проверка перехода
    - изменение сущности
    """
    ensure_can_change_payout_status(
        actor=actor,
        payout=payout,
        new_status=new_status,
    )
    validate_payout_status_transition(payout, new_status)

    payout.status = new_status.value
    return payout
