from django.db import models


class Recipient(models.Model):
    class Type(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        BUSINESS = "BUSINESS", "Business"

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INDIVIDUAL,
        help_text="Recipient type: individual or business.",
    )

    name = models.CharField(
        max_length=255,
        help_text="Full name or company name.",
    )

    account_number = models.CharField(
        max_length=64,
        help_text="Account/card/IBAN number in its original form.",
    )

    bank_code = models.CharField(
        max_length=32,
        blank=True,
        help_text="Bank identifier (MFO/BIC/SWIFT, etc.), if applicable.",
    )

    country = models.CharField(
        max_length=2,
        blank=True,
        help_text="Country code (ISO 3166-1 alpha-2), e.g. UA, US, PL.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this recipient can be used for new payouts.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the recipient was created.",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the recipient was last updated.",
    )

    class Meta:
        db_table = "payouts_recipient"
        verbose_name = "Payout recipient"
        verbose_name_plural = "Payout recipients"
        ordering = ("name", "id")

    def __str__(self) -> str:
        return (
            f"Recipient(id={self.pk}, name={self.name}, account={self.account_number})"
        )


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
        help_text="Recipient to whom the payout is sent.",
    )

    # Business parameters

    idempotency_key = models.CharField(
        max_length=64,
        unique=True,
        help_text="Key used for idempotent payout creation.",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Payout amount.",
    )

    currency = models.CharField(
        max_length=3,
        help_text="Currency code (ISO 4217, e.g. USD, EUR, UAH).",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Current payout status.",
        db_index=True,
    )

    # Snapshot of recipient details at payout creation time

    recipient_name_snapshot = models.CharField(
        max_length=255,
        help_text="Recipient name at the time of payout creation.",
    )

    account_number_snapshot = models.CharField(
        max_length=64,
        help_text="Recipient account number at the time of payout creation.",
    )

    bank_code_snapshot = models.CharField(
        max_length=32,
        blank=True,
        help_text="Bank identifier at the time of payout creation.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the payout request was created.",
        db_index=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the payout was last updated.",
    )

    class Meta:
        db_table = "payouts_payout"
        verbose_name = "Payout request"
        verbose_name_plural = "Payout requests"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=("status", "created_at"),
            ),
            models.Index(
                fields=("recipient", "created_at"),
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Payout(id={self.pk}, amount={self.amount} {self.currency}, "
            f"status={self.status}, recipient={self.recipient_name_snapshot})"
        )

    def fill_recipient_snapshot(self) -> None:
        """
        Populate recipient snapshot fields from the current recipient state.

        Called from the domain service when creating a payout.
        """
        self.recipient_name_snapshot = self.recipient.name
        self.account_number_snapshot = self.recipient.account_number
        self.bank_code_snapshot = self.recipient.bank_code
