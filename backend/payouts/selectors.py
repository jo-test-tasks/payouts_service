from .models import Payout


def list_payouts():
    """
    Base selector for listing payouts.
    Returns a queryset with deterministic ordering suitable for cursor pagination.
    """
    return Payout.objects.select_related("recipient").order_by("-created_at", "-id")
