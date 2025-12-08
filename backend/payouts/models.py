from django.db import models

from django.db import models


class Recipient(models.Model):
    class Type(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        BUSINESS = "BUSINESS", "Business"

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INDIVIDUAL,
        help_text="Тип получателя: физлицо или бизнес.",
    )

    name = models.CharField(
        max_length=255,
        help_text="Имя/ФИО или название компании.",
    )

    account_number = models.CharField(
        max_length=64,
        help_text="Номер карты/счёта/IBAN в исходном виде.",
    )

    bank_code = models.CharField(
        max_length=32,
        blank=True,
        help_text="Идентификатор банка (MFO/BIC/SWIFT и т.п.), если применимо.",
    )

    country = models.CharField(
        max_length=2,
        blank=True,
        help_text="Код страны (ISO 3166-1 alpha-2), например: UA, US, PL.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Можно ли сейчас использовать получателя для новых выплат.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда получатель был создан.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Когда получатель был изменён в последний раз.",
    )

    class Meta:
        db_table = "payouts_recipient"
        verbose_name = "Получатель выплаты"
        verbose_name_plural = "Получатели выплат"
        ordering = ("name", "id")

    def __str__(self) -> str:
        return f"Recipient(id={self.pk}, name={self.name}, account={self.account_number})"


class Payout(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    recipient = models.ForeignKey(
        "Recipient",
        on_delete=models.PROTECT,
        related_name="payouts",
        help_text="Получатель, которому отправляем деньги.",
    )

    # --- Бизнес-параметры выплаты ---

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Сумма выплаты.",
    )

    currency = models.CharField(
        max_length=3,
        help_text="Код валюты (ISO 4217, например: USD, EUR, UAH).",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Текущий статус заявки.",
    )

    # --- Снэпшот реквизитов получателя на момент создания выплаты ---

    recipient_name_snapshot = models.CharField(
        max_length=255,
        help_text="Имя/ФИО/название получателя на момент создания выплаты.",
    )

    account_number_snapshot = models.CharField(
        max_length=64,
        help_text="Номер карты/счёта получателя на момент создания выплаты.",
    )

    bank_code_snapshot = models.CharField(
        max_length=32,
        blank=True,
        help_text="Банковский идентификатор на момент создания выплаты.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Когда заявка была создана.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Когда заявка была изменена в последний раз.",
    )

    class Meta:
        db_table = "payouts_payout"
        verbose_name = "Заявка на выплату"
        verbose_name_plural = "Заявки на выплату"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return (
            f"Payout(id={self.pk}, amount={self.amount} {self.currency}, "
            f"status={self.status}, recipient={self.recipient_name_snapshot})"
        )

    # Не бизнес-логика, а утилита для доменного сервиса:
    def fill_recipient_snapshot(self) -> None:
        """
        Заполнить снэпшот реквизитов на основе текущего состояния recipient.

        Вызывается из доменного сервиса при создании заявки.
        """
        self.recipient_name_snapshot = self.recipient.name
        self.account_number_snapshot = self.recipient.account_number
        self.bank_code_snapshot = self.recipient.bank_code
