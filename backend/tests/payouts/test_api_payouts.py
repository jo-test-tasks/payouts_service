# backend/tests/payouts/test_api_payouts.py
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache  # 👈 ДОБАВИЛИ
from rest_framework.test import APIClient

from payouts.models import Recipient, Payout

User = get_user_model()


API_LIST_URL = "/api/payouts/"


@pytest.fixture(autouse=True)
def clear_cache():
    """
    Чистим кеш перед каждым тестом, чтобы
    старые закешированные страницы списка не мешали.
    """
    cache.clear()




@pytest.mark.django_db
class TestPayoutListCreateAPI:
    def setup_method(self):
        self.client = APIClient()

    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def test_list_payouts_initially_empty(self):
        response = self.client.get(API_LIST_URL)

        assert response.status_code == 200
        data = response.json()

        # теперь ответ пагинированный
        assert isinstance(data, dict)
        assert set(data.keys()) == {"next", "previous", "results"}
        assert data["results"] == []

    def test_list_payouts_returns_created_payouts(self):
        recipient = self._create_recipient()

        p1 = Payout.objects.create(
            recipient=recipient,
            amount=Decimal("10.00"),
            currency="USD",
            status=Payout.Status.NEW,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key="idem-list-1",
        )
        p2 = Payout.objects.create(
            recipient=recipient,
            amount=Decimal("20.00"),
            currency="EUR",
            status=Payout.Status.PROCESSING,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key="idem-list-2",
        )

        response = self.client.get(API_LIST_URL)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        assert "results" in data
        results = data["results"]

        # простой чек: два элемента и нужные id
        assert len(results) == 2
        returned_ids = {item["id"] for item in results}
        assert returned_ids == {p1.id, p2.id}

    def test_create_payout_success(self):
        recipient = self._create_recipient(is_active=True)

        payload = {
            "recipient_id": recipient.id,
            "amount": "100.50",
            "currency": "USD",
            "idempotency_key": "idem-api-create-1",
        }

        response = self.client.post(API_LIST_URL, data=payload, format="json")

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        payout_id = data["id"]

        payout = Payout.objects.get(pk=payout_id)
        assert payout.recipient == recipient
        assert payout.amount == Decimal("100.50")
        assert payout.currency == "USD"
        assert payout.status == Payout.Status.NEW

        assert payout.recipient_name_snapshot == recipient.name
        assert payout.account_number_snapshot == recipient.account_number
        assert payout.bank_code_snapshot == recipient.bank_code

    @pytest.mark.django_db
    def test_create_payout_idempotent_second_time_returns_200_and_same_id(self):
        recipient = self._create_recipient(is_active=True)

        payload = {
            "recipient_id": recipient.id,
            "amount": "50.00",
            "currency": "USD",
            "idempotency_key": "idem-api-dup-1",
        }

        first = self.client.post(API_LIST_URL, data=payload, format="json")
        second = self.client.post(API_LIST_URL, data=payload, format="json")

        assert first.status_code == 201
        assert second.status_code == 200

        first_data = first.json()
        second_data = second.json()
        assert first_data["id"] == second_data["id"]
        assert Payout.objects.count() == 1

    def test_create_payout_recipient_not_found_returns_404(self):
        payload = {
            "recipient_id": 9999,  # такого нет
            "amount": "50.00",
            "currency": "USD",
            "idempotency_key": "idem-api-not-found",
        }

        response = self.client.post(API_LIST_URL, data=payload, format="json")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.django_db
class TestPayoutDetailAPI:
    def setup_method(self):
        self.client = APIClient()

    def _create_recipient(self, *, is_active: bool = True) -> Recipient:
        return Recipient.objects.create(
            type=Recipient.Type.INDIVIDUAL,
            name="John Doe",
            account_number="UA1234567890",
            bank_code="MFO123",
            country="UA",
            is_active=is_active,
        )

    def _create_payout(self, status: str = Payout.Status.NEW) -> Payout:
        recipient = self._create_recipient()
        return Payout.objects.create(
            recipient=recipient,
            amount=Decimal("50.00"),
            currency="USD",
            status=status,
            recipient_name_snapshot=recipient.name,
            account_number_snapshot=recipient.account_number,
            bank_code_snapshot=recipient.bank_code,
            idempotency_key=f"idem-detail-{status}",
        )

    def test_get_payout_detail_success(self):
        payout = self._create_payout()

        url = f"/api/payouts/{payout.id}/"
        response = self.client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == payout.id
        assert data["amount"] == "50.00"
        assert data["currency"] == "USD"
        assert data["status"] == Payout.Status.NEW

    def test_get_payout_detail_not_found(self):
        url = "/api/payouts/9999/"
        response = self.client.get(url)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_delete_payout_success_as_staff(self):
        payout = self._create_payout()

        admin = User.objects.create_user(
            username="admin",
            password="adminpass",
            is_staff=True,
        )

        self.client.force_authenticate(user=admin)

        url = f"/api/payouts/{payout.id}/"
        response = self.client.delete(url)

        assert response.status_code == 204
        assert not Payout.objects.filter(id=payout.id).exists()

    def test_delete_payout_not_found_returns_404(self):
        admin = User.objects.create_user(
            username="admin",
            password="adminpass",
            is_staff=True,
        )
        self.client.force_authenticate(user=admin)

        url = "/api/payouts/9999/"
        response = self.client.delete(url)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_delete_payout_forbidden_for_anonymous(self):
        payout = self._create_payout()

        url = f"/api/payouts/{payout.id}/"
        # без аутентификации IsAdminUser должен порезать
        response = self.client.delete(url)

        assert response.status_code == 403
        assert Payout.objects.filter(id=payout.id).exists()

    def test_patch_payout_status_success_as_staff(self):
        payout = self._create_payout(status=Payout.Status.NEW)

        admin = User.objects.create_user(
            username="admin",
            password="adminpass",
            is_staff=True,
        )
        self.client.force_authenticate(user=admin)

        url = f"/api/payouts/{payout.id}/"
        payload = {"status": Payout.Status.PROCESSING}

        response = self.client.patch(url, data=payload, format="json")

        assert response.status_code == 200
        payout.refresh_from_db()
        assert payout.status == Payout.Status.PROCESSING

    def test_patch_payout_status_forbidden_for_non_staff(self):
        payout = self._create_payout(status=Payout.Status.NEW)

        user = User.objects.create_user(
            username="user",
            password="userpass",
            is_staff=False,
        )
        self.client.force_authenticate(user=user)

        url = f"/api/payouts/{payout.id}/"
        payload = {"status": Payout.Status.PROCESSING}

        response = self.client.patch(url, data=payload, format="json")

        assert response.status_code == 403
        payout.refresh_from_db()
        assert payout.status == Payout.Status.NEW

    def test_patch_payout_status_invalid_transition_returns_400(self):
        """
        COMPLETED → NEW запрещён валидатором validate_payout_status_transition.
        """
        payout = self._create_payout(status=Payout.Status.COMPLETED)

        admin = User.objects.create_user(
            username="admin2",
            password="adminpass2",
            is_staff=True,
        )
        self.client.force_authenticate(user=admin)

        url = f"/api/payouts/{payout.id}/"
        payload = {"status": Payout.Status.NEW}

        response = self.client.patch(url, data=payload, format="json")

        # set_payout_status должен кинуть DomainValidationError,
        # а custom_exception_handler → 400
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        payout.refresh_from_db()
        assert payout.status == Payout.Status.COMPLETED
