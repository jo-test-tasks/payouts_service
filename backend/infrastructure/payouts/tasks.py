from celery import shared_task
from .cache import bump_payouts_list_cache_version


@shared_task(bind=True, ignore_result=True)
def rebuild_payouts_cache_task(self) -> None:
    bump_payouts_list_cache_version()
