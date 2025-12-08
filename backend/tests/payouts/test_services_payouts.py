# backend/tests/payouts/test_services_payouts.py
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.exceptions import DomainValidationError, DomainPermissionError
from payouts.models import Recipient, Payout
from payouts.services import create_payout, set_payout_status


User = get_user_model()


# ============================================================================
# create_payout
# ============================================================================

@pytest.mark.django_db
def test_create_payout_success():
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )

    payout = create_payout(
        recipient=recipient,
        amount=Decimal("100.50"),
        currency="usd",  # специально в нижнем регистре, проверим .upper()
    )

    # Появился id → сохранён в БД
    assert payout.id is not None

    # Базовые поля
    assert payout.recipient == recipient
    assert payout.amount == Decimal("100.50")
    assert payout.currency == "USD"  # должен быть upper()

    # Статус по умолчанию
    assert payout.status == Payout.Status.NEW

    # Снэпшоты
    assert payout.recipient_name_snapshot == recipient.name
    assert payout.account_number_snapshot == recipient.account_number
    assert payout.bank_code_snapshot == recipient.bank_code


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["0", "-0.01", "-100"])
def test_create_payout_negative_amount_raises(value):
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )

    with pytest.raises(DomainValidationError) as exc:
        create_payout(
            recipient=recipient,
            amount=Decimal(value),
            currency="USD",
        )

    assert "Сумма выплаты должна быть больше нуля" in str(exc.value)


@pytest.mark.django_db
def test_create_payout_unsupported_currency_raises():
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )

    with pytest.raises(DomainValidationError) as exc:
        create_payout(
            recipient=recipient,
            amount=Decimal("10.00"),
            currency="BTC",  # не из SUPPORTED_CURRENCIES
        )

    assert "валюта не поддерживается" in str(exc.value)


@pytest.mark.django_db
def test_create_payout_inactive_recipient_raises():
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA1234567890",
        bank_code="MFO123",
        country="UA",
        is_active=False,
    )

    with pytest.raises(DomainValidationError) as exc:
        create_payout(
            recipient=recipient,
            amount=Decimal("10.00"),
            currency="USD",
        )

    assert "Нельзя создать выплату неактивному получателю" in str(exc.value)


# ============================================================================
# set_payout_status
# ============================================================================

@pytest.mark.django_db
def test_set_payout_status_success():
    # Подготовка: активный реципиент + payout в статусе NEW
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
    )

    # Актор — staff-пользователь
    actor = User.objects.create_user(
        username="admin",
        password="adminpass",
        is_staff=True,
    )

    updated = set_payout_status(
        payout=payout,
        new_status=Payout.Status.PROCESSING,
        actor=actor,
    )

    payout.refresh_from_db()

    assert updated.id == payout.id
    assert payout.status == Payout.Status.PROCESSING


@pytest.mark.django_db
@pytest.mark.parametrize(
    "actor_factory",
    [
        lambda: None,
        lambda: User.objects.create_user(
            username="regular",
            password="pass",
            is_staff=False,
        ),
    ],
)
def test_set_payout_status_non_staff_actor_raises(actor_factory):
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
    )

    actor = actor_factory()

    with pytest.raises(DomainPermissionError) as exc:
        set_payout_status(
            payout=payout,
            new_status=Payout.Status.PROCESSING,
            actor=actor,
        )

    assert "Недостаточно прав" in str(exc.value)

    payout.refresh_from_db()
    # Статус не должен поменяться
    assert payout.status == Payout.Status.NEW


@pytest.mark.django_db
def test_set_payout_status_invalid_transition_raises():
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
        status=Payout.Status.COMPLETED,
        recipient_name_snapshot=recipient.name,
        account_number_snapshot=recipient.account_number,
        bank_code_snapshot=recipient.bank_code,
    )

    actor = User.objects.create_user(
        username="admin",
        password="adminpass",
        is_staff=True,
    )

    # Пытаемся откатить COMPLETED → NEW — по правилам это запрещено
    with pytest.raises(DomainValidationError) as exc:
        set_payout_status(
            payout=payout,
            new_status=Payout.Status.NEW,
            actor=actor,
        )

    assert "Нельзя перевести выплату" in str(exc.value)

    payout.refresh_from_db()
    assert payout.status == Payout.Status.COMPLETED
