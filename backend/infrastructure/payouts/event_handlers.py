# infrastructure/payouts/event_handlers.py
from core.event_bus import event_bus
from payouts.events import PayoutCreated

from .tasks import rebuild_payouts_cache_task


def handle_payout_created(event: PayoutCreated) -> None:
    """
    Реакция на создание выплаты:
    инвалидировать/прогреть кеш через Celery.
    """
    rebuild_payouts_cache_task.delay()


# регистрируем подписчика при импорте модуля
event_bus.subscribe(PayoutCreated, handle_payout_created)
