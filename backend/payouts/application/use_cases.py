import logging

from django.db import IntegrityError, transaction

from core.event_bus import event_bus
from payouts.domain.services import (
    build_idempotency_key,
    build_money,
    build_new_payout,
    build_payout_status,
    change_status,
)
from payouts.events import PayoutCreated
from payouts.repositories import PayoutRepository, RecipientRepository

logger = logging.getLogger(__name__)


# payouts/application/use_cases.py
class CreatePayoutUseCase:
    """
    Application-level orchestration for creating payouts.

    Responsibilities:
    - Fetch required domain data (recipient)
    - Prepare Value Objects (Money, IdempotencyKey)
    - Coordinate domain services, repository, and event publishing
    - Handle idempotency and race conditions
    - Ensure transactional integrity

    This layer MUST NOT contain business rules — only orchestration.
    """

    @staticmethod
    @transaction.atomic
    def execute(*, recipient_id, amount, currency, idempotency_key):
        # Fetch recipient entity through repository abstraction
        recipient = RecipientRepository.get_by_id(recipient_id)

        # Convert primitives to domain Value Objects — domain boundary
        money = build_money(amount, currency)
        key = build_idempotency_key(idempotency_key)

        # Idempotency check BEFORE creating domain entity
        # This avoids duplicate payouts for the same external request
        existing = PayoutRepository.get_by_idempotency_key_or_none(key)
        if existing:
            logger.info(
                "Idempotent payout reuse: key=%s, payout_id=%s",
                key.value,
                existing.id,
            )
            return existing, True

        # Instantiate domain entity via factory — keeps business rules in domain layer
        payout = build_new_payout(
            recipient=recipient,
            money=money,
            key=key,
        )

        try:
            # Persist entity — repository encapsulates ORM details
            payout = PayoutRepository.save(payout)
        except IntegrityError:
            # Concurrent request with same idempotency key may cause DB constraint violation.
            # Resolve by reloading existing payout.
            payout = PayoutRepository.get_by_idempotency_key(key)

            logger.warning(
                "Idempotency race resolved: key=%s, payout_id=%s, recipient_id=%s",
                key.value,
                payout.id,
                recipient.id,
            )
            return payout, True

        logger.info(
            "Payout created: id=%s, recipient_id=%s, amount=%s %s",
            payout.id,
            recipient.id,
            money.amount,
            money.currency,
        )

        # Publish domain event AFTER transaction is committed.
        # Guarantees event is sent only if DB write succeeded.
        transaction.on_commit(
            lambda: event_bus.publish(PayoutCreated(payout_id=payout.id))
        )

        return payout, False


class ChangeStatusUseCase:
    """
    Application-level orchestration for updating payout status.

    Responsibilities:
    - Validate and convert status value into domain VO
    - Delegate business rule enforcement to domain service
    - Persist updated entity
    - Keep all operations transactional

    This layer coordinates; it does NOT implement business rules.
    """

    @staticmethod
    @transaction.atomic
    def execute(*, payout, new_status, actor):
        old_status = payout.status

        # Translate raw status into domain Value Object — ensures validity
        status_vo = build_payout_status(new_status)

        # Domain service applies business logic for status transitions
        payout = change_status(
            payout=payout,
            new_status=status_vo,
            actor=actor,
        )

        # Persist updated entity
        updated = PayoutRepository.save(payout)

        logger.info(
            "Payout status changed: id=%s, %s -> %s, actor=%s",
            updated.id,
            old_status,
            updated.status,
            getattr(actor, "id", None) if actor else "system",
        )

        return updated
