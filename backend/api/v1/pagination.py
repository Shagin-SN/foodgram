from rest_framework.pagination import PageNumberPagination

from .constants import DEFAULT_PAGE_LIMIT


class FoodgramLimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = DEFAULT_PAGE_LIMIT
