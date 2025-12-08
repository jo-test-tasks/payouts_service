# payouts/repositories.py
from decimal import Decimal
from typing import Optional

from core.exceptions import DomainNotFoundError
from .models import Recipient, Payout


class RecipientRepository:
    @staticmethod
    def get_recipient_by_id(recipient_id: int) -> Recipient:
        try:
            return Recipient.objects.get(pk=recipient_id)
        except Recipient.DoesNotExist:
            raise DomainNotFoundError("Recipient not found")


class PayoutRepository:
    @staticmethod
    def get_payout_by_id(payout_id: int) -> Payout:
        try:
            return (
                Payout.objects
                .select_related("recipient")
                .get(pk=payout_id)
            )
        except Payout.DoesNotExist:
            raise DomainNotFoundError("Payout not found")

    @staticmethod
    def get_payout_by_idempotency_key(idempotency_key: str) -> Payout:
        try:
            return (
                Payout.objects
                .select_related("recipient")
                .get(idempotency_key=idempotency_key)
            )
        except Payout.DoesNotExist:
            raise DomainNotFoundError("Payout not found")

    @staticmethod
    def get_payout_by_idempotency_key_or_none(idempotency_key: str) -> Optional[Payout]:
        return (
            Payout.objects
            .select_related("recipient")
            .filter(idempotency_key=idempotency_key)
            .first()
        )

    @staticmethod
    def create_payout(
        *,
        recipient: Recipient,
        amount: Decimal,
        currency: str,
        status: str,
        idempotency_key: str,
    ) -> Payout:
        payout = Payout(
            recipient=recipient,
            amount=amount,
            currency=currency,
            status=status,
            idempotency_key=idempotency_key,
        )
        payout.fill_recipient_snapshot()
        payout.save()
        return payout

    @staticmethod
    def update_payout_status(*, payout: Payout, new_status: str) -> Payout:
        payout.status = new_status
        payout.save(update_fields=["status", "updated_at"])
        return payout
