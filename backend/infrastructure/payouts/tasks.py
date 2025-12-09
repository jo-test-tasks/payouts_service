from celery import shared_task
from .cache import invalidate_payouts_list_cache, get_payouts_list_from_cache


@shared_task(bind=True, ignore_result=True)
def rebuild_payouts_list_cache_task(self) -> None:
    invalidate_payouts_list_cache()
    get_payouts_list_from_cache()
