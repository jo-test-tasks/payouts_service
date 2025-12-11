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
    Простая инфраструктурная задача:
    - bump версии кеша списка выплат;
    - при сбоях попробует несколько раз с backoff.
    """
    logger.info(
        "rebuild_payouts_cache_task started: task_id=%s",
        self.request.id,
    )

    try:
        bump_payouts_list_cache_version()
    except Exception:
        # log + проброс для autoretry_for
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
    Идемпотентная задача обработки выплаты:
    - безопасно обрабатывает повторные вызовы (после ретраев);
    - не падает, если выплаты уже нет;
    - меняет статус по простому сценарию NEW -> PROCESSING -> COMPLETED.
    """
    logger.info(
        "process_payout_task started: task_id=%s, payout_id=%s, retries=%s",
        self.request.id,
        payout_id,
        self.request.retries,
    )

    # 1) Пытаемся достать выплату
    try:
        payout = PayoutRepository.get_by_id(payout_id)
    except DomainNotFoundError:
        # Выплата уже удалена/не существует — логируем и выходим без ретраев
        logger.warning(
            "process_payout_task: payout not found, skipping. "
            "task_id=%s, payout_id=%s",
            self.request.id,
            payout_id,
        )
        return

    # 2) Идемпотентность: если уже в финальном статусе — просто выходим
    if payout.status in (Payout.Status.COMPLETED, Payout.Status.FAILED):
        logger.info(
            "process_payout_task: payout already in terminal state, skipping. "
            "task_id=%s, payout_id=%s, status=%s",
            self.request.id,
            payout_id,
            payout.status,
        )
        return

    # 3) Основной рабочий поток
    try:
        with transaction.atomic():
            # Шаг 1: помечаем как PROCESSING (если ещё NEW)
            if payout.status == Payout.Status.NEW:
                payout = ChangeStatusUseCase.execute(
                    payout=payout,
                    new_status=Payout.Status.PROCESSING,
                    actor=None,  # системный актор
                )
                logger.info(
                    "process_payout_task: payout moved to PROCESSING. "
                    "task_id=%s, payout_id=%s",
                    self.request.id,
                    payout_id,
                )

            # Здесь мог бы быть вызов внешнего платёжного провайдера:
            #
            # provider_response = external_provider.charge(...)
            # if not provider_response.ok:
            #     raise SomeProviderError(...)
            #
            # Для демо оставим мягкую "задержку":
            sleep(1)

            # Шаг 2: помечаем как COMPLETED (если всё ок)
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
        # Любая ошибка — лог + проброс для autoretry_for
        logger.exception(
            "process_payout_task failed: task_id=%s, payout_id=%s "
            "(will be retried if retries left)",
            self.request.id,
            payout_id,
        )
        raise
