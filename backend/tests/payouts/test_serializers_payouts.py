# backend/tests/payouts/test_serializers_payouts.py
from decimal import Decimal

import pytest

from payouts.models import Recipient, Payout
from payouts.serializers import (
    PayoutSerializer,
    PayoutCreateSerializer,
    PayoutPartialUpdateSerializer,
)


# ============================================================================
# PayoutCreateSerializer
# ============================================================================

def test_payout_create_serializer_valid_data():
    """
    Валидный payload → serializer.is_valid() == True,
    типы приведены корректно.
    """
    data = {
        "recipient_id": 1,           # сам факт существования recipient тут не проверяется
        "amount": "100.50",
        "currency": "USD",
    }

    serializer = PayoutCreateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    validated = serializer.validated_data
    assert validated["recipient_id"] == 1
    assert isinstance(validated["amount"], Decimal)
    assert validated["amount"] == Decimal("100.50")
    assert validated["currency"] == "USD"


def test_payout_create_serializer_missing_required_fields():
    """
    Отсутствие обязательных полей → ошибка валидации.
    """
    data = {}

    serializer = PayoutCreateSerializer(data=data)
    assert not serializer.is_valid()
    errors = serializer.errors

    assert "recipient_id" in errors
    assert "amount" in errors
    assert "currency" in errors


def test_payout_create_serializer_invalid_amount_format():
    """
    Некорректный формат суммы → ошибка.
    """
    data = {
        "recipient_id": 1,
        "amount": "not-a-decimal",
        "currency": "USD",
    }

    serializer = PayoutCreateSerializer(data=data)
    assert not serializer.is_valid()
    errors = serializer.errors
    assert "amount" in errors


def test_payout_create_serializer_currency_too_long():
    """
    Нарушение max_length=3 у currency → ошибка сериализатора.
    """
    data = {
        "recipient_id": 1,
        "amount": "10.00",
        "currency": "TOO_LONG",  # > 3 символов
    }

    serializer = PayoutCreateSerializer(data=data)
    assert not serializer.is_valid()
    errors = serializer.errors
    assert "currency" in errors


# ============================================================================
# PayoutPartialUpdateSerializer
# ============================================================================

def test_payout_partial_update_serializer_valid_status():
    """
    Корректный статус из choices → ок.
    """
    data = {"status": Payout.Status.PROCESSING}

    serializer = PayoutPartialUpdateSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    validated = serializer.validated_data
    assert validated["status"] == Payout.Status.PROCESSING


def test_payout_partial_update_serializer_invalid_status():
    """
    Статус вне choices → ошибка сериализатора (до домена не доходим).
    """
    data = {"status": "SOME_TRASH_STATUS"}

    serializer = PayoutPartialUpdateSerializer(data=data)
    assert not serializer.is_valid()
    errors = serializer.errors
    assert "status" in errors


# ============================================================================
# PayoutSerializer (read-only)
# ============================================================================

@pytest.mark.django_db
def test_payout_serializer_representation_basic_fields():
    """
    Проверяем, что PayoutSerializer корректно отдаёт основные поля,
    включая recipient_id (через source="recipient.id").
    """
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

    serializer = PayoutSerializer(payout)
    data = serializer.data

    # поля модели
    assert data["id"] == payout.id
    assert data["amount"] == "50.00"  # DRF DecimalField → строка
    assert data["currency"] == "USD"
    assert data["status"] == Payout.Status.NEW

    # наш кастомный recipient_id
    assert data["recipient_id"] == recipient.id

    # снэпшоты
    assert data["recipient_name_snapshot"] == recipient.name
    assert data["account_number_snapshot"] == recipient.account_number
    assert data["bank_code_snapshot"] == recipient.bank_code

    # технические поля
    assert "created_at" in data
    assert "updated_at" in data
