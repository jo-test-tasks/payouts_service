# payouts/repositories.py

from core.exceptions import DomainNotFoundError

from .models import Recipient, Payout


class RecipientRepository:
    @staticmethod
    def get_recipient_by_id(recipient_id: int) -> Recipient:
        try:
            return (
                Recipient.objects
                .get(pk=recipient_id)
            )
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

    