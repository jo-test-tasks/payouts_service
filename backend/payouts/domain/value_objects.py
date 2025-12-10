from dataclasses import dataclass
from decimal import Decimal

from core.exceptions import DomainValidationError
from payouts.models import Payout


SUPPORTED_CURRENCIES = {"USD", "EUR", "UAH"}


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        if self.amount <= 0:
            raise DomainValidationError("Сумма должна быть больше нуля.")
        code = (self.currency or "").upper()
        if code not in SUPPORTED_CURRENCIES:
            raise DomainValidationError("Валюта не поддерживается.")
        object.__setattr__(self, "currency", code)


@dataclass(frozen=True)
class IdempotencyKey:
    value: str

    def __post_init__(self):
        v = (self.value or "").strip()
        if not (8 <= len(v) <= 64):
            raise DomainValidationError("Неверная длина ключа идемпотентности.")
        object.__setattr__(self, "value", v)


@dataclass(frozen=True)
class PayoutStatus:
    value: str

    def __post_init__(self):
        raw = (self.value or "").upper()
        if raw not in Payout.Status.values:
            raise DomainValidationError("Некорректный статус выплаты.")
        object.__setattr__(self, "value", raw)
