# payouts/api/serializers.py
from rest_framework import serializers

from payouts.models import Recipient, Payout


class PayoutSerializer(serializers.ModelSerializer):
    recipient_id = serializers.IntegerField(source="recipient.id", read_only=True)

    class Meta:
        model = Payout
        fields = [
            "id",
            "recipient_id",
            "amount",
            "currency",
            "status",
            "recipient_name_snapshot",
            "account_number_snapshot",
            "bank_code_snapshot",
            "created_at",
            "updated_at",
        ]


class PayoutCreateSerializer(serializers.ModelSerializer):
    recipient_id = serializers.IntegerField()
    idempotency_key = serializers.CharField(write_only=True)

    class Meta:
        model = Payout
        fields = ["recipient_id", "amount", "currency", "idempotency_key"]


class PayoutPartialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ["status"]
