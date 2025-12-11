from django.urls import path

from .api import PayoutDetailAPIView, PayoutListCreateAPIView

urlpatterns = [
    # GET  /api/payouts/     — list payouts
    # POST /api/payouts/     — create payout
    path("", PayoutListCreateAPIView.as_view(), name="payouts-list-create"),

    # GET    /api/payouts/<id>/ — retrieve payout
    # PATCH  /api/payouts/<id>/ — update status
    # DELETE /api/payouts/<id>/ — delete payout
    path("<int:pk>/", PayoutDetailAPIView.as_view(), name="payouts-detail"),
]
