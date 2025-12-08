# backend/tests/payouts/test_validators.py
from decimal import Decimal

import pytest

from core.exceptions import DomainValidationError, DomainPermissionError
from payouts.models import Recipient, Payout
from payouts.validators import (
    SUPPORTED_CURRENCIES,
    validate_amount_positive,
    validate_currency_code,
    validate_recipient_basic,
    validate_recipient_active,
    validate_payout_status_transition,
    ensure_can_change_payout_status,
)


# ============================================================
# validate_amount_positive
# ============================================================

def test_validate_amount_positive_ok():
    # не должно кидать исключение
    validate_amount_positive(Decimal("0.01"))
    validate_amount_positive(Decimal("100"))


@pytest.mark.parametrize("value", ["0", "-0.01", "-100"])
def test_validate_amount_positive_raises_on_zero_or_negative(value):
    with pytest.raises(DomainValidationError) as exc:
        validate_amount_positive(Decimal(value))
    assert "больше нуля" in str(exc.value)


# ============================================================
# validate_currency_code
# ============================================================

@pytest.mark.parametrize("code", list(SUPPORTED_CURRENCIES))
def test_validate_currency_code_ok(code):
    # любые поддерживаемые коды должны проходить
    validate_currency_code(code)
    validate_currency_code(code.lower())  # проверка, что upper() работает


@pytest.mark.parametrize("code", ["", "US", "BITCOIN", "123", "U4H"])
def test_validate_currency_code_unsupported_raises(code):
    with pytest.raises(DomainValidationError) as exc:
        validate_currency_code(code)
    assert "не поддерживается" in str(exc.value)


# ============================================================
# validate_recipient_basic
# ============================================================

def test_validate_recipient_basic_ok():
    # нормальное имя и номер счёта
    validate_recipient_basic("John Doe", "UA12 3456 7890")
    validate_recipient_basic("A B", "1234-5678-90")


@pytest.mark.parametrize("name", ["", " ", "A"])
def test_validate_recipient_basic_short_name_raises(name):
    with pytest.raises(DomainValidationError) as exc:
        validate_recipient_basic(name, "12345678")
    assert "Имя получателя слишком короткое" in str(exc.value)


@pytest.mark.parametrize("number", ["", "1234567", "12-34-56"])
def test_validate_recipient_basic_short_account_number_raises(number):
    with pytest.raises(DomainValidationError) as exc:
        validate_recipient_basic("John Doe", number)
    assert "Номер счёта/карты слишком короткий" in str(exc.value)


@pytest.mark.parametrize("number", ["1234-56!78", "1234 5678 #", "****1234"])
def test_validate_recipient_basic_illegal_chars_raises(number):
    with pytest.raises(DomainValidationError) as exc:
        validate_recipient_basic("John Doe", number)
    assert "недопустимые символы" in str(exc.value)


# ============================================================
# validate_recipient_active
# ============================================================

@pytest.mark.django_db
def test_validate_recipient_active_ok():
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA12345678",
        bank_code="MFO123",
        country="UA",
        is_active=True,
    )
    # не должно кидать исключение
    validate_recipient_active(recipient)


@pytest.mark.django_db
def test_validate_recipient_active_inactive_raises():
    recipient = Recipient.objects.create(
        type=Recipient.Type.INDIVIDUAL,
        name="John Doe",
        account_number="UA12345678",
        bank_code="MFO123",
        country="UA",
        is_active=False,
    )
    with pytest.raises(DomainValidationError) as exc:
        validate_recipient_active(recipient)
    assert "неактивному получателю" in str(exc.value)


# ============================================================
# validate_payout_status_transition
# ============================================================

def _make_payout(status: str) -> Payout:
    # можно не сохранять в БД — для валидатора достаточно инстанса
    return Payout(
        status=status,
        amount=Decimal("10.00"),
        currency="USD",
        recipient_name_snapshot="Test",
        account_number_snapshot="12345678",
        bank_code_snapshot="MFO123",
    )


@pytest.mark.parametrize(
    "old_status,new_status",
    [
        (Payout.Status.NEW, Payout.Status.PROCESSING),
        (Payout.Status.NEW, Payout.Status.FAILED),
        (Payout.Status.PROCESSING, Payout.Status.COMPLETED),
        (Payout.Status.PROCESSING, Payout.Status.FAILED),
    ],
)
def test_validate_payout_status_transition_allowed(old_status, new_status):
    payout = _make_payout(old_status)
    # не должно кидать
    validate_payout_status_transition(payout, new_status)


@pytest.mark.parametrize(
    "old_status,new_status",
    [
        (Payout.Status.NEW, Payout.Status.COMPLETED),
        (Payout.Status.PROCESSING, Payout.Status.NEW),
        (Payout.Status.COMPLETED, Payout.Status.NEW),
        (Payout.Status.COMPLETED, Payout.Status.PROCESSING),
        (Payout.Status.FAILED, Payout.Status.NEW),
    ],
)
def test_validate_payout_status_transition_forbidden_raises(old_status, new_status):
    payout = _make_payout(old_status)
    with pytest.raises(DomainValidationError) as exc:
        validate_payout_status_transition(payout, new_status)
    assert "Нельзя перевести выплату" in str(exc.value)


def test_validate_payout_status_transition_invalid_new_status_raises():
    payout = _make_payout(Payout.Status.NEW)
    with pytest.raises(DomainValidationError) as exc:
        validate_payout_status_transition(payout, "SOME_TRASH_STATUS")
    assert "Некорректный статус" in str(exc.value)


# ============================================================
# ensure_can_change_payout_status
# ============================================================

class DummyUser:
    def __init__(self, is_staff: bool):
        self.is_staff = is_staff


def test_ensure_can_change_payout_status_staff_ok():
    actor = DummyUser(is_staff=True)
    payout = _make_payout(Payout.Status.NEW)
    # не должно кидать
    ensure_can_change_payout_status(actor=actor, payout=payout, new_status=Payout.Status.PROCESSING)


@pytest.mark.parametrize(
    "actor",
    [
        None,
        DummyUser(is_staff=False),
    ],
)
def test_ensure_can_change_payout_status_non_staff_raises(actor):
    payout = _make_payout(Payout.Status.NEW)
    with pytest.raises(DomainPermissionError) as exc:
        ensure_can_change_payout_status(actor=actor, payout=payout, new_status=Payout.Status.PROCESSING)
    assert "Недостаточно прав" in str(exc.value)
