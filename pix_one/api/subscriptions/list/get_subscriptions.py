import frappe
from frappe import _
from pix_one.common.shared import get_pagination_params, BaseDataService
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions
from pix_one.common.cache import RedisCacheService


@frappe.whitelist()
@handle_exceptions
def get_subscriptions(page=1, limit=10, sort=None, order=None, search=None, status=None, customer_id=None):
	"""
	Get paginated list of subscriptions

	Args:
		page: Page number (default: 1)
		limit: Items per page (default: 10, max: 100)
		sort: Sort field (default: creation)
		order: Sort order - 'asc' or 'desc' (default: desc)
		search: Search term (searches in plan_name, customer_id)
		status: Filter by status
		customer_id: Filter by customer

	Returns:
		Paginated list of subscriptions
	"""
	# Setup pagination
	pagination = get_pagination_params(
		page=page,
		limit=limit,
		sort=sort or 'creation',
		order=order or 'desc',
		search=search,
		fields='*'
	)

	# Build filters
	filters = []

	# Filter by customer if not admin
	if not frappe.has_permission('SaaS Subscriptions', 'read'):
		# Regular users can only see their own subscriptions
		filters.append(['customer_id', '=', frappe.session.user])
	elif customer_id:
		# Admin can filter by specific customer
		filters.append(['customer_id', '=', customer_id])

	# Filter by status if provided
	if status:
		filters.append(['status', '=', status])

	# Setup cache key
	cache_key = f"subscriptions:list:{page}:{limit}:{sort}:{order}:{search}:{status}:{customer_id}:{frappe.session.user}"

	# Try to get from cache
	cached_data = RedisCacheService.get(cache_key)
	if cached_data:
		return cached_data

	# Get paginated data
	data, total = BaseDataService.get_paginated_data(
		doctype='SaaS Subscriptions',
		pagination=pagination,
		additional_filters=filters,
		search_fields=['plan_name', 'customer_id', 'app_name', 'license_key']
	)

	# Enrich data with plan details
	for subscription in data:
		if subscription.get('plan_name'):
			plan = frappe.db.get_value(
				'SaaS Subscription Plan',
				subscription['plan_name'],
				['plan_name', 'short_description', 'billing_interval', 'price'],
				as_dict=True
			)
			subscription['plan_details'] = plan

		# Get customer name
		if subscription.get('customer_id'):
			customer_name = frappe.db.get_value('User', subscription['customer_id'], 'full_name')
			subscription['customer_name'] = customer_name

	# Prepare response
	response = ResponseFormatter.paginated(
		data=data,
		total=total,
		page=pagination.page,
		limit=pagination.limit,
		message="Subscriptions retrieved successfully"
	)

	# Cache the response for 2 minutes
	RedisCacheService.set(cache_key, response, expires_in_sec=120)

	return response


@frappe.whitelist()
@handle_exceptions
def get_my_subscriptions(page=1, limit=10, sort=None, order=None, status=None):
	"""
	Get current user's subscriptions

	Args:
		page: Page number (default: 1)
		limit: Items per page (default: 10, max: 100)
		sort: Sort field (default: creation)
		order: Sort order - 'asc' or 'desc' (default: desc)
		status: Filter by status

	Returns:
		Paginated list of user's subscriptions
	"""
	return get_subscriptions(
		page=page,
		limit=limit,
		sort=sort,
		order=order,
		status=status,
		customer_id=frappe.session.user
	)


@frappe.whitelist()
@handle_exceptions
def get_subscription_stats(customer_id=None):
	"""
	Get subscription statistics

	Args:
		customer_id: Customer ID (optional, defaults to current user for non-admin)

	Returns:
		Subscription statistics
	"""
	# Determine customer
	if not customer_id or not frappe.has_permission('SaaS Subscriptions', 'read'):
		customer_id = frappe.session.user

	# Get statistics
	stats = {
		'total': BaseDataService.count_records('SaaS Subscriptions', [['customer_id', '=', customer_id]]),
		'active': BaseDataService.count_records('SaaS Subscriptions', [
			['customer_id', '=', customer_id],
			['status', '=', 'Active']
		]),
		'trial': BaseDataService.count_records('SaaS Subscriptions', [
			['customer_id', '=', customer_id],
			['status', '=', 'Trial']
		]),
		'expired': BaseDataService.count_records('SaaS Subscriptions', [
			['customer_id', '=', customer_id],
			['status', '=', 'Expired']
		]),
		'cancelled': BaseDataService.count_records('SaaS Subscriptions', [
			['customer_id', '=', customer_id],
			['status', '=', 'Cancelled']
		]),
		'pending': BaseDataService.count_records('SaaS Subscriptions', [
			['customer_id', '=', customer_id],
			['status', '=', 'Pending Payment']
		])
	}

	return ResponseFormatter.success(
		data=stats,
		message="Subscription statistics retrieved successfully"
	)
