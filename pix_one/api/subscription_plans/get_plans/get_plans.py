import frappe
from pix_one.common.shared.base_pagination import get_pagination_params
from pix_one.common.shared.base_data_service import BaseDataService
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions
from pix_one.common.cache.redis_cache_service import RedisCacheService


@frappe.whitelist(allow_guest=True)
@handle_exceptions
def get_subscription_plans(page=1, limit=10, sort=None, order=None, search=None, fields='*', filters=None):
    """
    Get subscription plans with pagination

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 10, max: 100)
        sort: Field to sort by
        order: Sort order ('asc' or 'desc')
        search: Search term (searches in plan_name and description)
        fields: Fields to return (default: all)
        filters: Additional filters as dict

    Returns:
        Paginated response with subscription plans
    """
    # Get pagination parameters
    pagination = get_pagination_params(
        page=page,
        limit=limit,
        sort=sort,
        order=order,
        search=search,
        fields=fields,
        filters=filters
    )

    # Build cache key
    cache_key = f"subscription_plans:{pagination.page}:{pagination.limit}:{pagination.sort}:{pagination.order}:{pagination.search}"

    # Try to get from cache
    cached_data = RedisCacheService.get(cache_key)
    if cached_data:
        return cached_data

    # Define search fields for subscription plans
    search_fields = ['plan_name', 'description']

    # Get paginated data
    plans, total_count = BaseDataService.get_paginated_data(
        doctype="Subscription Plan",
        pagination=pagination,
        search_fields=search_fields
    )

    # Format response
    response = ResponseFormatter.paginated(
        data=plans,
        total=total_count,
        page=pagination.page,
        limit=pagination.limit,
        message="Subscription plans retrieved successfully"
    )

    # Cache the response for 5 minutes
    RedisCacheService.set(cache_key, response, expires_in_sec=300)

    return response