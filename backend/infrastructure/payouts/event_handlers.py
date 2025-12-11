# infrastructure/payouts/event_handlers.py
from core.event_bus import event_bus
from payouts.events import PayoutCreated

from .tasks import process_payout_task, rebuild_payouts_cache_task


def handle_payout_created(event: PayoutCreated) -> None:
    """
    Handles payout creation:
    - invalidates payouts list cache
    - triggers asynchronous payout processing
    """
    rebuild_payouts_cache_task.delay()
    process_payout_task.delay(event.payout_id)


# Register event handler on module import
event_bus.subscribe(PayoutCreated, handle_payout_created)
