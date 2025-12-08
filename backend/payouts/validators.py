# payouts/validators.py
from decimal import Decimal
from typing import Iterable

from core.exceptions import DomainValidationError, DomainPermissionError

from .models import Recipient, Payout

# Для учебного проекта можно зашить поддерживаемые валюты константой.
SUPPORTED_CURRENCIES = {"USD", "EUR", "UAH"}


def validate_amount_positive(amount: Decimal) -> None:
    """
    Доменная проверка суммы:
    - сумма должна быть > 0.
    """
    # Здесь amount уже гарантированно не None,
    # т.к. сериализатор проверяет required и тип.
    if amount <= 0:
        raise DomainValidationError("Сумма выплаты должна быть больше нуля.")


def validate_currency_code(currency: str) -> None:
    """
    Доменная проверка валюты:
    - длина ровно 3 символа;
    - только буквы;
    - должна быть в списке поддерживаемых валют.
    """
    code = (currency or "").upper()


    if code not in SUPPORTED_CURRENCIES:
        raise DomainValidationError("Данная валюта не поддерживается системой.")


def validate_recipient_basic(name: str, account_number: str) -> None:
    """
    Базовая проверка реципиента:
    - осмысленное имя;
    - не слишком короткий номер счёта/карты;
    - допустимые символы.
    """
    if not name or len(name.strip()) < 2:
        raise DomainValidationError("Имя получателя слишком короткое.")

    normalized = (account_number or "").replace(" ", "").replace("-", "")

    if len(normalized) < 8:
        raise DomainValidationError("Номер счёта/карты слишком короткий.")

    if not normalized.isalnum():
        raise DomainValidationError("Номер счёта/карты содержит недопустимые символы.")


def validate_recipient_active(recipient: Recipient) -> None:
    """
    Нельзя создавать выплаты неактивному получателю.
    """
    if not recipient.is_active:
        raise DomainValidationError("Нельзя создать выплату неактивному получателю.")


def validate_payout_status_transition(payout: Payout, new_status: str) -> None:
    """
    Простая state-machine для статусов выплаты.
    """
    allowed_transitions: dict[str, Iterable[str]] = {
        Payout.Status.NEW: {Payout.Status.PROCESSING, Payout.Status.FAILED},
        Payout.Status.PROCESSING: {Payout.Status.COMPLETED, Payout.Status.FAILED},
        Payout.Status.COMPLETED: set(),
        Payout.Status.FAILED: set(),
    }

    if new_status not in Payout.Status.values:
        raise DomainValidationError("Некорректный статус выплаты.")

    allowed = set(allowed_transitions.get(payout.status, set()))
    if new_status not in allowed:
        raise DomainValidationError(
            f"Нельзя перевести выплату из статуса {payout.status} в {new_status}."
        )

def ensure_can_change_payout_status(*, actor, payout: Payout, new_status: str) -> None:
    """
    Проверка прав на смену статуса выплаты.
    Здесь можно зашить простое правило:
    - только staff-пользователь может менять статус.
    """

    # Если системы авторизации пока нет — можешь временно закомментировать,
    # но для "по уму" делаем так:
    if actor is None or not getattr(actor, "is_staff", False):
        raise DomainPermissionError("Недостаточно прав для смены статуса выплаты.")