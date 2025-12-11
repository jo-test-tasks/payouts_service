# backend/infrastructure/payouts/cache.py
import logging
from urllib.parse import urlencode

from django.core.cache import cache
from rest_framework.response import Response

logger = logging.getLogger(__name__)

PAYOUTS_LIST_CACHE_VERSION_KEY = "payouts:list:version"
PAYOUTS_LIST_PAGE_TTL = 60  # seconds


def safe_cache_get(key, default=None):
    """Fail-safe wrapper around cache.get()."""
    try:
        return cache.get(key, default)
    except Exception:
        logger.warning("Cache get failed for key=%s", key, exc_info=True)
        return default


def safe_cache_set(key, value, timeout=None):
    """Fail-safe wrapper around cache.set()."""
    try:
        cache.set(key, value, timeout=timeout)
    except Exception:
        logger.warning("Cache set failed for key=%s", key, exc_info=True)


def _get_payouts_list_cache_version() -> int:
    """
    Returns the current cache version for payouts list.
    Version bump invalidates all cached pages automatically.
    """
    version = safe_cache_get(PAYOUTS_LIST_CACHE_VERSION_KEY)
    if version is None:
        version = 1
        safe_cache_set(PAYOUTS_LIST_CACHE_VERSION_KEY, version, None)
    return int(version)


def bump_payouts_list_cache_version() -> None:
    """
    Invalidate cached payout list pages by incrementing the global version.
    """
    try:
        cache.incr(PAYOUTS_LIST_CACHE_VERSION_KEY)
    except Exception:
        logger.warning(
            "Cache incr failed for key=%s, resetting to 2",
            PAYOUTS_LIST_CACHE_VERSION_KEY,
            exc_info=True,
        )
        safe_cache_set(PAYOUTS_LIST_CACHE_VERSION_KEY, 2, None)


def _build_payouts_page_cache_key(request) -> str:
    """
    Builds a deterministic cache key based on:
    - request path
    - sorted query parameters
    - current cache version
    """
    version = _get_payouts_list_cache_version()

    items = sorted(request.query_params.items())
    query_string = urlencode(items)

    return f"payouts:list:v{version}:path={request.path}?{query_string}"


def get_paginated_payouts_response_with_cache(
    request,
    base_queryset,
    paginator,
    serializer_class,
):
    """
    Returns a paginated DRF Response object.
    Uses cache for storing fully rendered paginated JSON payloads.
    """
    cache_key = _build_payouts_page_cache_key(request)

    cached_data = safe_cache_get(cache_key)
    if cached_data is not None:
        return Response(cached_data)

    # Query database when no cached page is found
    page = paginator.paginate_queryset(base_queryset, request)
    serializer = serializer_class(page, many=True)
    response = paginator.get_paginated_response(serializer.data)

    # Cache the serialized page result
    safe_cache_set(cache_key, response.data, timeout=PAYOUTS_LIST_PAGE_TTL)

    return response
