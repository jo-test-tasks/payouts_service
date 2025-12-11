import logging
from time import sleep

from celery import shared_task
from django.db import transaction

from core.exceptions import DomainNotFoundError
from payouts.application.use_cases import ChangeStatusUseCase
from payouts.models import Payout
from payouts.repositories import PayoutRepository

from .cache import bump_payouts_list_cache_version

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
    ignore_result=True,
)
def rebuild_payouts_cache_task(self) -> None:
    """
    Infrastructure task:
    - increments global payouts list cache version
    - retries automatically with exponential backoff on failure
    """
    logger.info(
        "rebuild_payouts_cache_task started: task_id=%s",
        self.request.id,
    )

    try:
        bump_payouts_list_cache_version()
    except Exception:
        logger.exception(
            "rebuild_payouts_cache_task failed: task_id=%s (will be retried)",
            self.request.id,
        )
        raise

    logger.info(
        "rebuild_payouts_cache_task completed: task_id=%s",
        self.request.id,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
    ignore_result=True,
)
def process_payout_task(self, payout_id: int) -> None:
    """
    Idempotent payout processing task:
    - handles repeat executions safely (Celery retries)
    - exits gracefully if payout no longer exists
    - transitions payout through NEW → PROCESSING → COMPLETED
    """
    logger.info(
        "process_payout_task started: task_id=%s, payout_id=%s, retries=%s",
        self.request.id,
        payout_id,
        self.request.retries,
    )

    # 1) Fetch payout
    try:
        payout = PayoutRepository.get_by_id(payout_id)
    except DomainNotFoundError:
        logger.warning(
            "process_payout_task: payout not found, skipping. "
            "task_id=%s, payout_id=%s",
            self.request.id,
            payout_id,
        )
        return

    # 2) Idempotency: skip if payout already in terminal state
    if payout.status in (Payout.Status.COMPLETED, Payout.Status.FAILED):
        logger.info(
            "process_payout_task: payout already in terminal state, skipping. "
            "task_id=%s, payout_id=%s, status=%s",
            self.request.id,
            payout_id,
            payout.status,
        )
        return

    # 3) Main processing flow
    try:
        with transaction.atomic():

            # Step 1: move NEW → PROCESSING
            if payout.status == Payout.Status.NEW:
                payout = ChangeStatusUseCase.execute(
                    payout=payout,
                    new_status=Payout.Status.PROCESSING,
                    actor=None,  # system actor
                )
                logger.info(
                    "process_payout_task: payout moved to PROCESSING. "
                    "task_id=%s, payout_id=%s",
                    self.request.id,
                    payout_id,
                )

            # Placeholder for external provider call
            # sleep() simulates network delay
            sleep(1)

            # Step 2: move PROCESSING → COMPLETED
            payout = ChangeStatusUseCase.execute(
                payout=payout,
                new_status=Payout.Status.COMPLETED,
                actor=None,
            )

        logger.info(
            "process_payout_task completed successfully: "
            "task_id=%s, payout_id=%s, final_status=%s",
            self.request.id,
            payout_id,
            payout.status,
        )

    except Exception:
        logger.exception(
            "process_payout_task failed: task_id=%s, payout_id=%s "
            "(will be retried if retries left)",
            self.request.id,
            payout_id,
        )
        raise
