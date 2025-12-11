from typing import Optional

from core.exceptions import DomainNotFoundError
from payouts.domain.value_objects import IdempotencyKey
from payouts.models import Payout, Recipient


class RecipientRepository:
    @staticmethod
    def get_by_id(recipient_id: int) -> Recipient:
        try:
            return Recipient.objects.get(pk=recipient_id)
        except Recipient.DoesNotExist:
            raise DomainNotFoundError("Recipient not found")


class PayoutRepository:
    @staticmethod
    def get_by_id(payout_id: int) -> Payout:
        try:
            return Payout.objects.select_related("recipient").get(pk=payout_id)
        except Payout.DoesNotExist:
            raise DomainNotFoundError("Payout not found")

    @staticmethod
    def get_by_idempotency_key_or_none(key: IdempotencyKey) -> Optional[Payout]:
        return (
            Payout.objects.select_related("recipient")
            .filter(idempotency_key=key.value)
            .first()
        )

    @staticmethod
    def get_by_idempotency_key(key: IdempotencyKey) -> Payout:
        try:
            return Payout.objects.select_related("recipient").get(
                idempotency_key=key.value
            )
        except Payout.DoesNotExist:
            raise DomainNotFoundError("Payout not found")

    @staticmethod
    def save(payout: Payout) -> Payout:
        """
        Repository layer does not contain business logic.
        It receives a fully constructed domain entity and simply persists it.
        """
        payout.save()
        return payout
