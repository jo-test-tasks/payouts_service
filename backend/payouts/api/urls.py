from django.urls import path

from .api import (
    PayoutListCreateAPIView,
    PayoutDetailAPIView,
)

urlpatterns = [
    # GET  /api/payouts/      — список выплат
    # POST /api/payouts/      — создание выплаты
    path("", PayoutListCreateAPIView.as_view(), name="payouts-list-create"),
    # GET    /api/payouts/<id>/ — получить выплату
    # PATCH  /api/payouts/<id>/ — изменить статус
    # DELETE /api/payouts/<id>/ — удалить выплату
    path("<int:pk>/", PayoutDetailAPIView.as_view(), name="payouts-detail")
]

