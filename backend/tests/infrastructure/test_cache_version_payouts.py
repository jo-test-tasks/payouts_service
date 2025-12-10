# tests/payouts/test_cache_version_payouts.py
import pytest
from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from infrastructure.payouts.cache import (
    _build_payouts_page_cache_key,
    _get_payouts_list_cache_version,
    bump_payouts_list_cache_version,
)


@pytest.mark.django_db
def test_bump_payouts_list_cache_version_changes_cache_key():
    factory = APIRequestFactory()

    # Django WSGIRequest
    django_request = factory.get("/api/payouts/", {"cursor": "abc"})
    # Оборачиваем в DRF Request, чтобы был .query_params
    request = Request(django_request)

    cache.clear()

    key_before = _build_payouts_page_cache_key(request)
    version_before = _get_payouts_list_cache_version()

    bump_payouts_list_cache_version()

    key_after = _build_payouts_page_cache_key(request)
    version_after = _get_payouts_list_cache_version()

    assert version_after == version_before + 1
    assert key_before != key_after
