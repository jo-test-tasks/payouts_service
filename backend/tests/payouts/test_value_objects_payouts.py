from decimal import Decimal

import pytest

from core.exceptions import DomainValidationError
from payouts.domain.value_objects import IdempotencyKey, Money, PayoutStatus
from payouts.models import Payout


class TestMoneyVO:
    def test_money_valid_normalizes_currency_to_upper(self):
        m = Money(amount=Decimal("10.50"), currency="usd")
        assert m.amount == Decimal("10.50")
        assert m.currency == "USD"

    def test_money_negative_amount_raises(self):
        with pytest.raises(DomainValidationError):
            Money(amount=Decimal("-1.00"), currency="USD")

    def test_money_unsupported_currency_raises(self):
        with pytest.raises(DomainValidationError):
            Money(amount=Decimal("10.00"), currency="XYZ")


class TestIdempotencyKeyVO:
    def test_idempotency_key_trims_and_stores_value(self):
        key = IdempotencyKey("   some-key-123   ")
        assert key.value == "some-key-123"

    def test_idempotency_key_too_short_raises(self):
        with pytest.raises(DomainValidationError):
            IdempotencyKey("short")

    def test_idempotency_key_too_long_raises(self):
        with pytest.raises(DomainValidationError):
            IdempotencyKey("x" * 65)


class TestPayoutStatusVO:
    def test_payout_status_valid_normalizes_to_upper(self):
        s = PayoutStatus("new")
        assert s.value == Payout.Status.NEW

    def test_payout_status_invalid_raises(self):
        with pytest.raises(DomainValidationError):
            PayoutStatus("INVALID_STATUS")
