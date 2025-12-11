# payouts/api/api.py
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from infrastructure.payouts.cache import get_paginated_payouts_response_with_cache
from payouts.api.serializers import (
    PayoutCreateSerializer,
    PayoutPartialUpdateSerializer,
    PayoutSerializer,
)
from payouts.application.use_cases import ChangeStatusUseCase, CreatePayoutUseCase
from payouts.pagination import PayoutCursorPagination
from payouts.repositories import PayoutRepository
from payouts.selectors import list_payouts


class PayoutListCreateAPIView(APIView):
    """
    GET /api/payouts/  — список заявок
    POST /api/payouts/ — создание заявки
    """

    permission_classes = [AllowAny]
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

        payout, is_duplicate = CreatePayoutUseCase.execute(
            recipient_id=recipient_id,
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

    def get_permissions(self):
        if self.request.method in ("PATCH", "DELETE"):
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request, pk: int):
        payout = PayoutRepository.get_by_id(pk)
        serializer = PayoutSerializer(payout)
        return Response(serializer.data)

    def patch(self, request, pk: int):
        payout = PayoutRepository.get_by_id(pk)

        serializer = PayoutPartialUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]

        updated = ChangeStatusUseCase.execute(
            payout=payout,
            new_status=new_status,
            actor=request.user,
        )

        return Response(PayoutSerializer(updated).data, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        payout = PayoutRepository.get_by_id(pk)
        payout.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
