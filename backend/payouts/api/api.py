# payouts/api/api.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from payouts.pagination import PayoutCursorPagination
from infrastructure.payouts.cache import (
    get_paginated_payouts_response_with_cache,
)


from payouts.serializers import (
    PayoutSerializer,
    PayoutCreateSerializer,
    PayoutPartialUpdateSerializer,
)

from payouts.selectors import (
    list_payouts,
)

from payouts.repositories import (
    RecipientRepository,
    PayoutRepository,
)

from payouts.services import (
    create_payout,
    set_payout_status
)


class PayoutListCreateAPIView(APIView):
    """
    GET /api/payouts/  — список заявок
    POST /api/payouts/ — создание заявки
    """

    permission_classes = [AllowAny]  # при желании можно ограничить
    pagination_class = PayoutCursorPagination

    def get(self, request):
        qs = list_payouts()
        paginator = self.pagination_class()
        
        return get_paginated_payouts_response_with_cache(
            request=request,
            base_queryset=qs,
            paginator=paginator,
            serializer_class=PayoutSerializer,
        )

    def post(self, request):
        serializer = PayoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipient_id = serializer.validated_data["recipient_id"]
        amount = serializer.validated_data["amount"]
        currency = serializer.validated_data["currency"]
        idempotency_key = serializer.validated_data["idempotency_key"]

        recipient = RecipientRepository.get_recipient_by_id(recipient_id)

        payout, is_duplicate = create_payout(
            recipient=recipient,
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
        )

        response_data = PayoutSerializer(payout).data
        status_code = status.HTTP_200_OK if is_duplicate else status.HTTP_201_CREATED

        return Response(response_data, status=status_code)


class PayoutDetailAPIView(APIView):
    """
    GET    /api/payouts/{id}/ — получение заявки
    PATCH  /api/payouts/{id}/ — смена статуса
    DELETE /api/payouts/{id}/ — удаление заявки
    """

    # GET может быть публичным, PATCH/DELETE — только staff.
    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAdminUser()]
        return [AllowAny()]


    def get(self, request, pk: int):
        payout = PayoutRepository.get_payout_by_id(pk)
        serializer = PayoutSerializer(payout)
        return Response(serializer.data)

    def patch(self, request, pk: int):
        payout = PayoutRepository.get_payout_by_id(pk)

        serializer = PayoutPartialUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        
        updated = set_payout_status(
                payout=payout,
                new_status=new_status,
                actor=request.user,
            )
        

        return Response(PayoutSerializer(updated).data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        payout = PayoutRepository.get_payout_by_id(pk)
        payout.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

