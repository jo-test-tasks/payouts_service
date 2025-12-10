# backend/tests/payouts/test_tasks_payouts.py
from decimal import Decimal

import pytest

from payouts.models import Recipient, Payout
from infrastructure.payouts.tasks import process_payout_task


@pytest.mark.django_db
def test_process_payout_task_changes_status_to_completed():
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )

    payout = Payout.objects.create(
        recipient=recipient,
        amount=Decimal("50.00"),
        currency="USD",
        status=Payout.Status.NEW,
        recipient_name_snapshot=recipient.name,
        account_number_snapshot=recipient.account_number,
        bank_code_snapshot=recipient.bank_code,
        idempotency_key="idem-task-1",
    )

    # Вызываем таску синхронно — без celery worker
    process_payout_task(payout.id)

    payout.refresh_from_db()
    assert payout.status == Payout.Status.COMPLETED
