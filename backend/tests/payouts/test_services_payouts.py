from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.exceptions import DomainPermissionError, DomainValidationError
from payouts.domain.services import (
    build_idempotency_key,
    build_money,
    build_new_payout,
    build_payout_status,
    change_status,
)
from payouts.models import Payout, Recipient

User = get_user_model()


@pytest.mark.django_db
class TestBuildNewPayoutService:
    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def test_build_new_payout_success(self):
        recipient = self._create_recipient(is_active=True)

        money = build_money(Decimal("100.50"), "usd")
        key = build_idempotency_key("idem-service-1")

        payout = build_new_payout(
            recipient=recipient,
            money=money,
            key=key,
        )

        # Entity factory should not persist the payout
        assert payout.pk is None
        assert payout.recipient == recipient
        assert payout.amount == Decimal("100.50")
        assert payout.currency == "USD"
        assert payout.status == Payout.Status.NEW
        assert payout.idempotency_key == "idem-service-1"
        assert payout.recipient_name_snapshot == recipient.name
        assert payout.account_number_snapshot == recipient.account_number
        assert payout.bank_code_snapshot == recipient.bank_code

    def test_build_new_payout_inactive_recipient_raises(self):
        recipient = self._create_recipient(is_active=False)

        money = build_money(Decimal("50.00"), "USD")
        key = build_idempotency_key("idem-service-2")

        with pytest.raises(DomainValidationError):
            build_new_payout(
                recipient=recipient,
                money=money,
                key=key,
            )


@pytest.mark.django_db
class TestChangeStatusService:
    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def _create_payout(
        self, *, status: str = Payout.Status.NEW, is_active_recipient: bool = True
    ) -> Payout:
        recipient = self._create_recipient(is_active=is_active_recipient)
        return Payout.objects.create(
            recipient=recipient,
            amount=Decimal("10.00"),
            currency="USD",
            status=status,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key=f"idem-service-{status}",
        )

    def _create_user(self, *, is_staff: bool) -> User:
        return User.objects.create_user(
            username="staff" if is_staff else "user",
            password="pass",
            is_staff=is_staff,
        )

    def test_change_status_success(self):
        payout = self._create_payout(status=Payout.Status.NEW, is_active_recipient=True)
        admin = self._create_user(is_staff=True)

        new_status_vo = build_payout_status(Payout.Status.PROCESSING)

        updated = change_status(
            payout=payout,
            new_status=new_status_vo,
            actor=admin,
        )

        assert updated.status == Payout.Status.PROCESSING

    def test_change_status_forbidden_for_non_staff(self):
        payout = self._create_payout(status=Payout.Status.NEW)
        user = self._create_user(is_staff=False)
        new_status_vo = build_payout_status(Payout.Status.PROCESSING)

        with pytest.raises(DomainPermissionError):
            change_status(
                payout=payout,
                new_status=new_status_vo,
                actor=user,
            )

        payout.refresh_from_db()
        assert payout.status == Payout.Status.NEW

    def test_change_status_invalid_transition_raises(self):
        payout = self._create_payout(status=Payout.Status.COMPLETED)
        admin = self._create_user(is_staff=True)
        new_status_vo = build_payout_status(Payout.Status.NEW)

        with pytest.raises(DomainValidationError):
            change_status(
                payout=payout,
                new_status=new_status_vo,
                actor=admin,
            )

        payout.refresh_from_db()
        assert payout.status == Payout.Status.COMPLETED

    def test_change_status_recipient_inactive_forward_blocked(self):
        payout = self._create_payout(
            status=Payout.Status.NEW,
            is_active_recipient=False,
        )
        admin = self._create_user(is_staff=True)
        new_status_vo = build_payout_status(Payout.Status.PROCESSING)

        with pytest.raises(DomainValidationError):
            change_status(
                payout=payout,
                new_status=new_status_vo,
                actor=admin,
            )

        payout.refresh_from_db()
        assert payout.status == Payout.Status.NEW
