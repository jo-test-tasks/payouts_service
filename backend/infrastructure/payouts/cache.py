# backend/infrastructure/payouts/cache.py

from urllib.parse import urlencode

from django.core.cache import cache
from rest_framework.response import Response


PAYOUTS_LIST_CACHE_VERSION_KEY = "payouts:list:version"
PAYOUTS_LIST_PAGE_TTL = 60  # сек, можешь потом подкрутить


def _get_payouts_list_cache_version() -> int:
    """
    Глобальная версия кеша списка выплат.
    При изменении данных мы просто увеличиваем версию,
    и старые страницы автоматически становятся "протухшими".
    """
    version = cache.get(PAYOUTS_LIST_CACHE_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(PAYOUTS_LIST_CACHE_VERSION_KEY, version, None)
    return int(version)


def bump_payouts_list_cache_version() -> None:
    """
    Инвалидация кеша всех страниц через bump версии.
    """
    try:
        cache.incr(PAYOUTS_LIST_CACHE_VERSION_KEY)
    except ValueError:
        # ключа ещё нет — просто выставим 2 как следующее значение
        cache.set(PAYOUTS_LIST_CACHE_VERSION_KEY, 2, None)


def _build_payouts_page_cache_key(request) -> str:
    """
    Ключ зависит:
    - от URL (path)
    - от query-параметров (особенно cursor)
    - от версии кеша
    """
    version = _get_payouts_list_cache_version()

    # Нормализуем query-параметры: сортируем, чтобы порядок в URL не влиял
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
    Возвращает DRF Response с пагинированным списком выплат,
    используя кеш готового ответа (JSON-структуры), привязанного к курсору.
    """
    cache_key = _build_payouts_page_cache_key(request)

    cached_data = cache.get(cache_key)
    if cached_data is not None:
        # cached_data — это dict/OrderedDict с полями cursor-пагинации
        return Response(cached_data)

    # Ходим в БД, если кеша нет
    page = paginator.paginate_queryset(base_queryset, request)
    serializer = serializer_class(page, many=True)
    response = paginator.get_paginated_response(serializer.data)

    # Сохраняем уже готовый payload (response.data) в кеш
    cache.set(cache_key, response.data, timeout=PAYOUTS_LIST_PAGE_TTL)

    return response
