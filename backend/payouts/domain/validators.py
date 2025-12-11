# payouts/domain/validators.py

from core.exceptions import DomainPermissionError, DomainValidationError
from payouts.domain.value_objects import PayoutStatus
from payouts.models import Payout, Recipient


def validate_recipient_active(
    recipient: Recipient,
    *,
    message: str | None = None,
) -> None:
    """
    Basic domain check ensuring the recipient is active.

    :param recipient: recipient entity
    :param message: optional custom error message
    """
    if not recipient.is_active:
        raise DomainValidationError(message or "Recipient is not active.")


def validate_payout_status_transition(
    payout: Payout,
    new_status: PayoutStatus,
) -> None:
    """
    Validate that the payout status transition is allowed.
    Includes a rule for inactive recipients.
    """
    allowed_transitions: dict[str, set[str]] = {
        Payout.Status.NEW: {Payout.Status.PROCESSING, Payout.Status.FAILED},
        Payout.Status.PROCESSING: {Payout.Status.COMPLETED, Payout.Status.FAILED},
        Payout.Status.COMPLETED: set(),
        Payout.Status.FAILED: set(),
    }

    new_value = new_status.value

    # Domain rule for inactive recipient — reuse shared validator
    validate_recipient_active(
        payout.recipient,
        message="Cannot process payout: recipient is no longer active.",
    )

    current_status = payout.status
    allowed = allowed_transitions.get(current_status, set())

    if new_value not in allowed:
        raise DomainValidationError(
            f"Invalid status transition from {current_status} to {new_value}"
        )


def ensure_can_change_payout_status(
    *,
    actor,
    payout: Payout,
    new_status: PayoutStatus,
) -> None:
    """
    Domain-level permission check for changing payout status.

    - HTTP requests pass actor=request.user
    - System calls (Celery, etc.) use actor=None
    """
    # System calls (Celery, etc.) use actor=None
    if actor is None:
        return

    if not getattr(actor, "is_staff", False):
        raise DomainPermissionError("Insufficient permissions.")
