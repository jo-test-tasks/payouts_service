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
            return payout, True

        transaction.on_commit(
            lambda: event_bus.publish(PayoutCreated(payout_id=payout.id))
        )

        return payout, False



class ChangeStatusUseCase:
    @staticmethod
    @transaction.atomic
    def execute(*, payout, new_status, actor):
        # граница домена: здесь мы превращаем примитив в VO
        status_vo = build_payout_status(new_status)

        payout = change_status(
            payout=payout,
            new_status=status_vo,
            actor=actor,
        )

        updated = PayoutRepository.save(payout)
        return updated
