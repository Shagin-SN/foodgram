from rest_framework.pagination import LimitOffsetPagination

from .constants import DEFAULT_PAGE_LIMIT


class FoodgramLimitOffsetPagination(LimitOffsetPagination):
    default_limit = DEFAULT_PAGE_LIMIT
