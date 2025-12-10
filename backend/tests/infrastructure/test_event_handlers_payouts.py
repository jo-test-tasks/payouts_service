# backend/tests/payouts/test_event_handlers_payouts.py
from unittest.mock import patch

from payouts.events import PayoutCreated
from infrastructure.payouts import event_handlers


def test_handle_payout_created_triggers_celery_tasks():
    event = PayoutCreated(payout_id=123)

    with patch("infrastructure.payouts.event_handlers.rebuild_payouts_cache_task.delay") as mock_rebuild_delay, \
         patch("infrastructure.payouts.event_handlers.process_payout_task.delay") as mock_process_delay:
        event_handlers.handle_payout_created(event)

    mock_rebuild_delay.assert_called_once_with()
    mock_process_delay.assert_called_once_with(123)
