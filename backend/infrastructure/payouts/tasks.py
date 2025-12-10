from celery import shared_task
from .cache import bump_payouts_list_cache_version
from django.db import transaction

from payouts.models import Payout
from payouts.application.use_cases import ChangeStatusUseCase
from payouts.repositories import PayoutRepository



@shared_task(bind=True, ignore_result=True)
def rebuild_payouts_cache_task(self) -> None:
    bump_payouts_list_cache_version()


@shared_task
def process_payout_task(payout_id: int) -> None:
    import time
    # имитация задержки
    # import time; time.sleep(1)
    payout = PayoutRepository.get_by_id(payout_id)
    
    time.sleep(1)
    # простая логика: NEW -> PROCESSING -> COMPLETED
    with transaction.atomic():
        ChangeStatusUseCase.execute(
            payout=payout,
            new_status=Payout.Status.PROCESSING,
            actor=None,   # в твоём домене можно сделать спец-актора "system"
        )

        time.sleep(1)
        ChangeStatusUseCase.execute(
            payout=payout,
            new_status=Payout.Status.COMPLETED,
            actor=None,
        )