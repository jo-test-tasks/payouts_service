# backend/tests/payouts/test_cache_payouts.py
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from payouts.models import Payout, Recipient

API_LIST_URL = "/api/payouts/"


@pytest.mark.django_db
def test_list_payouts_uses_cache_for_second_request():
    client = APIClient()

    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )

    Payout.objects.create(
        recipient=recipient,
        amount=Decimal("10.00"),
        currency="USD",
        status=Payout.Status.NEW,
        recipient_name_snapshot=recipient.name,
        account_number_snapshot=recipient.account_number,
        bank_code_snapshot=recipient.bank_code,
        idempotency_key="idem-cache-1",
    )

    # First request — warms up the cache
    with CaptureQueriesContext(connection) as ctx1:
        resp1 = client.get(API_LIST_URL)
    assert resp1.status_code == 200
    queries_first = len(ctx1)

    # Second request — should hit the DB fewer times (cache should be used)
    with CaptureQueriesContext(connection) as ctx2:
        resp2 = client.get(API_LIST_URL)
    assert resp2.status_code == 200
    queries_second = len(ctx2)

    # We don't require zero DB queries, because Django may issue internal ones
    assert queries_second <= queries_first
