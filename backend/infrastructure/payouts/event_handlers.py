# infrastructure/payouts/event_handlers.py
from core.event_bus import event_bus
from payouts.events import PayoutCreated

from .tasks import (
    rebuild_payouts_cache_task,
    process_payout_task,
)


def handle_payout_created(event: PayoutCreated) -> None:
    """
    Реакция на создание выплаты:
    - инвалидировать кеш списка выплат
    - запустить асинхронную обработку выплаты
    """
    rebuild_payouts_cache_task.delay()
    process_payout_task.delay(event.payout_id)


# регистрируем подписчика при импорте модуля
event_bus.subscribe(PayoutCreated, handle_payout_created)
