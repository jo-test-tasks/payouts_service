# payouts/domain/validators.py
from core.exceptions import DomainValidationError, DomainPermissionError
from payouts.models import Recipient, Payout
from payouts.domain.value_objects import PayoutStatus


def validate_recipient_active(recipient: Recipient):
    if not recipient.is_active:
        raise DomainValidationError("Получатель не активен.")


def validate_payout_status_transition(payout: Payout, new_status: PayoutStatus):
    allowed_transitions = {
        Payout.Status.NEW: {Payout.Status.PROCESSING, Payout.Status.FAILED},
        Payout.Status.PROCESSING: {Payout.Status.COMPLETED, Payout.Status.FAILED},
        Payout.Status.COMPLETED: set(),
        Payout.Status.FAILED: set(),
    }

    new_value = new_status.value

    # доменное правило про неактивного получателя
    if not payout.recipient.is_active and new_value in {
        Payout.Status.PROCESSING,
        Payout.Status.COMPLETED,
    }:
        raise DomainValidationError(
            "Нельзя обработать выплату: получатель больше не активен."
        )

    allowed = allowed_transitions.get(payout.status, set())
    if new_value not in allowed:
        raise DomainValidationError(
            f"Нельзя перевести из {payout.status} в {new_value}"
        )


def ensure_can_change_payout_status(*, actor, payout: Payout, new_status: PayoutStatus):
    if not getattr(actor, "is_staff", False):
        raise DomainPermissionError("Недостаточно прав.")
