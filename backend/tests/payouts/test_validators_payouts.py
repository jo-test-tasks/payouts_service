from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.exceptions import DomainValidationError, DomainPermissionError
from payouts.domain.validators import (
    validate_recipient_active,
    validate_payout_status_transition,
    ensure_can_change_payout_status,
)
from payouts.domain.value_objects import PayoutStatus
from payouts.models import Recipient, Payout

User = get_user_model()


@pytest.mark.django_db
class TestRecipientValidators:
    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def test_validate_recipient_active_ok_for_active(self):
        recipient = self._create_recipient(is_active=True)
        # не должно кидать исключение
        validate_recipient_active(recipient)

    def test_validate_recipient_active_raises_for_inactive(self):
        recipient = self._create_recipient(is_active=False)
        with pytest.raises(DomainValidationError):
            validate_recipient_active(recipient)


@pytest.mark.django_db
class TestPayoutStatusValidators:
    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def _create_payout(self, status: str, is_active_recipient: bool = True) -> Payout:
        recipient = self._create_recipient(is_active=is_active_recipient)
        return Payout.objects.create(
            recipient=recipient,
            amount=Decimal("10.00"),
            currency="USD",
            status=status,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key=f"idem-{status}",
        )

    def test_validate_payout_status_transition_allowed(self):
        payout = self._create_payout(status=Payout.Status.NEW)
        new_status = PayoutStatus(Payout.Status.PROCESSING)

        # не должно кидать исключение
        validate_payout_status_transition(payout, new_status)

    def test_validate_payout_status_transition_forbidden(self):
        payout = self._create_payout(status=Payout.Status.COMPLETED)
        new_status = PayoutStatus(Payout.Status.NEW)

        with pytest.raises(DomainValidationError):
            validate_payout_status_transition(payout, new_status)

    def test_validate_payout_status_transition_block_inactive_recipient(self):
        payout = self._create_payout(
            status=Payout.Status.NEW,
            is_active_recipient=False,
        )
        new_status = PayoutStatus(Payout.Status.PROCESSING)

        with pytest.raises(DomainValidationError):
            validate_payout_status_transition(payout, new_status)


@pytest.mark.django_db
class TestPermissionValidators:
    def _create_recipient(self) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=True,
        )

    def _create_payout(self, status: str = Payout.Status.NEW) -> Payout:
        recipient = self._create_recipient()
        return Payout.objects.create(
            recipient=recipient,
            amount=Decimal("10.00"),
            currency="USD",
            status=status,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key=f"idem-{status}",
        )

    def _create_user(self, *, is_staff: bool) -> User:
        return User.objects.create_user(
            username="staff" if is_staff else "user",
            password="pass",
            is_staff=is_staff,
        )

    def test_ensure_can_change_payout_status_ok_for_staff(self):
        payout = self._create_payout()
        admin = self._create_user(is_staff=True)

        new_status = PayoutStatus(Payout.Status.PROCESSING)
        # не должно кидать исключение
        ensure_can_change_payout_status(
            actor=admin,
            payout=payout,
            new_status=new_status,
        )

    def test_ensure_can_change_payout_status_forbidden_for_non_staff(self):
        payout = self._create_payout()
        user = self._create_user(is_staff=False)
        new_status = PayoutStatus(Payout.Status.PROCESSING)

        with pytest.raises(DomainPermissionError):
            ensure_can_change_payout_status(
                actor=user,
                payout=payout,
                new_status=new_status,
            )
