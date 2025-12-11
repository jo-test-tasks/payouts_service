from django.apps import AppConfig


class PayoutsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payouts"

    def ready(self) -> None:
        # При старте Django регистрируем инфраструктурные подписчики на события
        import infrastructure.payouts.event_handlers  # noqa: F401
