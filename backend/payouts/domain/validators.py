# payouts/domain/validators.py

from core.exceptions import DomainValidationError, DomainPermissionError
from payouts.models import Recipient, Payout
from payouts.domain.value_objects import PayoutStatus


def validate_recipient_active(
    recipient: Recipient,
    *,
    message: str | None = None,
) -> None:
    """
    Базовая доменная проверка, что получатель активен.

    :param recipient: объект получателя
    :param message: кастомный текст ошибки (опционально)
    """
    if not recipient.is_active:
        raise DomainValidationError(message or "Получатель не активен.")


def validate_payout_status_transition(
    payout: Payout,
    new_status: PayoutStatus,
) -> None:
    """
    Доменная проверка допустимости перехода статуса выплаты.
    Включает правило про неактивного получателя.
    """
    allowed_transitions: dict[str, set[str]] = {
        Payout.Status.NEW: {Payout.Status.PROCESSING, Payout.Status.FAILED},
        Payout.Status.PROCESSING: {Payout.Status.COMPLETED, Payout.Status.FAILED},
        Payout.Status.COMPLETED: set(),
        Payout.Status.FAILED: set(),
    }

    new_value = new_status.value

    # доменное правило про неактивного получателя — используем базовый валидатор
    validate_recipient_active(
        payout.recipient,
        message="Нельзя обработать выплату: получатель больше не активен.",
    )

    current_status = payout.status
    allowed = allowed_transitions.get(current_status, set())

    if new_value not in allowed:
        raise DomainValidationError(
            f"Нельзя перевести из {current_status} в {new_value}"
        )


def ensure_can_change_payout_status(
    *,
    actor,
    payout: Payout,
    new_status: PayoutStatus,
) -> None:
    """
    Доменная проверка прав на изменение статуса выплаты.
    - HTTP-запросы приходят с actor=request.user
    - Системные вызовы (Celery и т.п.) идут с actor=None
    """
    # Системные вызовы (Celery и пр.) идут с actor=None
    if actor is None:
        return

    if not getattr(actor, "is_staff", False):
        raise DomainPermissionError("Недостаточно прав.")
