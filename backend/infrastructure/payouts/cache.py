from django.core.cache import cache
from payouts.selectors import list_payouts

PAYOUTS_LIST_CACHE_KEY = "payouts:list"
PAYOUTS_LIST_TTL = 60


def get_payouts_list_from_cache():
    payouts = cache.get(PAYOUTS_LIST_CACHE_KEY)
    if payouts is not None:
        return payouts

    payouts = list(list_payouts())
    cache.set(PAYOUTS_LIST_CACHE_KEY, payouts, timeout=PAYOUTS_LIST_TTL)
    return payouts


def invalidate_payouts_list_cache() -> None:
    cache.delete(PAYOUTS_LIST_CACHE_KEY)
