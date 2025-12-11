# payouts/events.py
from dataclasses import dataclass


@dataclass(frozen=True)
class PayoutCreated:
    payout_id: int


@dataclass(frozen=True)
class PayoutStatusChanged:
    payout_id: int
    old_status: str
    new_status: str
