# backend/tests/payouts/test_use_cases_payouts.py
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.exceptions import DomainPermissionError, DomainValidationError
from payouts.application.use_cases import ChangeStatusUseCase, CreatePayoutUseCase
from payouts.models import Payout, Recipient

User = get_user_model()


@pytest.mark.django_db
class TestCreatePayoutUseCase:
    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def test_create_payout_success(self):
        recipient = self._create_recipient(is_active=True)

        payout, is_duplicate = CreatePayoutUseCase.execute(
            recipient_id=recipient.id,
            amount=Decimal("100.50"),
            currency="USD",
            idempotency_key="idem-usecase-1",
        )

        assert is_duplicate is False
        assert payout.id is not None
        assert payout.recipient == recipient
        assert payout.amount == Decimal("100.50")
        assert payout.currency == "USD"
        assert payout.status == Payout.Status.NEW

    def test_create_payout_recipient_inactive_raises(self):
        recipient = self._create_recipient(is_active=False)

        with pytest.raises(DomainValidationError):
            CreatePayoutUseCase.execute(
                recipient_id=recipient.id,
                amount=Decimal("50.00"),
                currency="USD",
                idempotency_key="idem-usecase-2",
            )

    def test_create_payout_idempotent_returns_existing(self):
        recipient = self._create_recipient(is_active=True)

        first_payout, is_dup_1 = CreatePayoutUseCase.execute(
            recipient_id=recipient.id,
            amount=Decimal("10.00"),
            currency="USD",
            idempotency_key="idem-usecase-3",
        )
        second_payout, is_dup_2 = CreatePayoutUseCase.execute(
            recipient_id=recipient.id,
            amount=Decimal("999.99"),  # даже если сумма другая
            currency="USD",
            idempotency_key="idem-usecase-3",
        )

        assert is_dup_1 is False
        assert is_dup_2 is True
        assert first_payout.id == second_payout.id
        assert Payout.objects.count() == 1


@pytest.mark.django_db
class TestChangeStatusUseCase:
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
        self, *, status: str = Payout.Status.NEW, is_active_recipient=True
    ) -> Payout:
        recipient = self._create_recipient(is_active=is_active_recipient)
        return Payout.objects.create(
            recipient=recipient,
            amount=Decimal("50.00"),
            currency="USD",
            status=status,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key=f"idem-status-{status}",
        )

    def _create_user(self, *, is_staff: bool) -> User:
        return User.objects.create_user(
            username="staff" if is_staff else "user",
            password="pass",
            is_staff=is_staff,
        )

    def test_change_status_success_as_staff(self):
        payout = self._create_payout(status=Payout.Status.NEW, is_active_recipient=True)
        admin = self._create_user(is_staff=True)

        updated = ChangeStatusUseCase.execute(
            payout=payout,
            new_status=Payout.Status.PROCESSING,
            actor=admin,
        )

        updated.refresh_from_db()
        assert updated.status == Payout.Status.PROCESSING

    def test_change_status_forbidden_for_non_staff(self):
        payout = self._create_payout(status=Payout.Status.NEW)
        user = self._create_user(is_staff=False)

        with pytest.raises(DomainPermissionError):
            ChangeStatusUseCase.execute(
                payout=payout,
                new_status=Payout.Status.PROCESSING,
                actor=user,
            )

        payout.refresh_from_db()
        assert payout.status == Payout.Status.NEW

    def test_change_status_invalid_transition_raises(self):
        """
        COMPLETED → NEW должно ломаться по state-machine.
        """
        payout = self._create_payout(status=Payout.Status.COMPLETED)
        admin = self._create_user(is_staff=True)

        with pytest.raises(DomainValidationError):
            ChangeStatusUseCase.execute(
                payout=payout,
                new_status=Payout.Status.NEW,
                actor=admin,
            )

        payout.refresh_from_db()
        assert payout.status == Payout.Status.COMPLETED

    def test_change_status_recipient_inactive_block_forward(self):
        """
        Если получатель стал неактивным — нельзя двигать выплату в PROCESSING/COMPLETED.
        (Это наше новое доменное правило)
        """
        payout = self._create_payout(
            status=Payout.Status.NEW,
            is_active_recipient=False,
        )
        admin = self._create_user(is_staff=True)

        with pytest.raises(DomainValidationError):
            ChangeStatusUseCase.execute(
                payout=payout,
                new_status=Payout.Status.PROCESSING,
                actor=admin,
            )

        payout.refresh_from_db()
        assert payout.status == Payout.Status.NEW
