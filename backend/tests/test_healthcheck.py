# backend/tests/test_healthcheck.py
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_healthcheck_basic():
    client = APIClient()
    resp = client.get("/health/")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "database" in data
    assert "redis" in data
    assert "status" in data
