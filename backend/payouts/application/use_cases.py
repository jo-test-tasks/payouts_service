import logging
from django.db import transaction, IntegrityError

from payouts.domain.services import (
    build_money,
    build_idempotency_key,
    build_payout_status,
    change_status,
    build_new_payout,
)

from payouts.repositories import (
    PayoutRepository,
    RecipientRepository,
)
from payouts.events import PayoutCreated
from core.event_bus import event_bus

logger = logging.getLogger(__name__)

# payouts/application/use_cases.py
class CreatePayoutUseCase:
    @staticmethod
    @transaction.atomic
    def execute(*, recipient_id, amount, currency, idempotency_key):
        recipient = RecipientRepository.get_by_id(recipient_id)

        money = build_money(amount, currency)
        key = build_idempotency_key(idempotency_key)

        existing = PayoutRepository.get_by_idempotency_key_or_none(key)
        if existing:
            logger.info(
                "Idempotent payout reuse: key=%s, payout_id=%s",
                key.value,
                existing.id,
            )
            return existing, True

        # строим доменную сущность через фабрику
        payout = build_new_payout(
            recipient=recipient,
            money=money,
            key=key,
        )

        try:
            payout = PayoutRepository.save(payout)
        except IntegrityError:
            # при гонке достаём по ключу
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
        transaction.on_commit(
            lambda: event_bus.publish(PayoutCreated(payout_id=payout.id))
        )

        return payout, False



class ChangeStatusUseCase:
    @staticmethod
    @transaction.atomic
    def execute(*, payout, new_status, actor):
        old_status = payout.status
        # граница домена: здесь мы превращаем примитив в VO
        status_vo = build_payout_status(new_status)

        payout = change_status(
            payout=payout,
            new_status=status_vo,
            actor=actor,
        )

        updated = PayoutRepository.save(payout)

        logger.info(
            "Payout status changed: id=%s, %s -> %s, actor=%s",
            updated.id,
            old_status,
            updated.status,
            getattr(actor, "id", None) if actor else "system",
        )
        return updated
