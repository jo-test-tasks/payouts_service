# backend/tests/payouts/test_celery_integration_payouts.py
from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from payouts.models import Recipient

API_LIST_URL = "/api/payouts/"


@pytest.mark.django_db(transaction=True)
def test_create_payout_triggers_celery_tasks_via_event_bus():
    client = APIClient()

    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )

    payload = {
        "recipient_id": recipient.id,
        "amount": "100.00",
        "currency": "USD",
        "idempotency_key": "idem-celery-1",
    }

    # Патчим именно там, где handle_payout_created дергает .delay(...)
    with patch("infrastructure.payouts.event_handlers.process_payout_task.delay") as mock_process_delay, \
         patch("infrastructure.payouts.event_handlers.rebuild_payouts_cache_task.delay") as mock_rebuild_delay:
        response = client.post(API_LIST_URL, data=payload, format="json")

    assert response.status_code == 201
    data = response.json()
    payout_id = data["id"]

    mock_process_delay.assert_called_once_with(payout_id)
    mock_rebuild_delay.assert_called_once_with()
