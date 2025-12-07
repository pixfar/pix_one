import frappe
from frappe import _
from pix_one.common.shared import get_pagination_params, BaseDataService
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions
from pix_one.common.cache import RedisCacheService


@frappe.whitelist()
@handle_exceptions
def get_transactions(page=1, limit=10, sort=None, order=None, search=None,
					status=None, transaction_type=None, customer_id=None, subscription_id=None):
	"""
	Get paginated list of payment transactions

	Args:
		page: Page number (default: 1)
		limit: Items per page (default: 10, max: 100)
		sort: Sort field (default: payment_date)
		order: Sort order - 'asc' or 'desc' (default: desc)
		search: Search term
		status: Filter by status
		transaction_type: Filter by transaction type
		customer_id: Filter by customer
		subscription_id: Filter by subscription

	Returns:
		Paginated list of transactions
	"""
	# Setup pagination
	pagination = get_pagination_params(
		page=page,
		limit=limit,
		sort=sort or 'payment_date',
		order=order or 'desc',
		search=search,
		fields='*'
	)

	# Build filters
	filters = []

	# Check permissions
	if not frappe.has_permission('SaaS Payment Transaction', 'read'):
		# Regular users can only see their own transactions
		filters.append(['customer_id', '=', frappe.session.user])
	elif customer_id:
		# Admin can filter by specific customer
		filters.append(['customer_id', '=', customer_id])

	# Filter by status
	if status:
		filters.append(['status', '=', status])

	# Filter by transaction type
	if transaction_type:
		filters.append(['transaction_type', '=', transaction_type])

	# Filter by subscription
	if subscription_id:
		filters.append(['subscription_id', '=', subscription_id])

	# Setup cache key
	cache_key = f"transactions:list:{page}:{limit}:{sort}:{order}:{search}:{status}:{transaction_type}:{customer_id}:{subscription_id}:{frappe.session.user}"

	# Try to get from cache
	cached_data = RedisCacheService.get(cache_key)
	if cached_data:
		return cached_data

	# Get paginated data
	data, total = BaseDataService.get_paginated_data(
		doctype='SaaS Payment Transaction',
		pagination=pagination,
		additional_filters=filters,
		search_fields=['transaction_id', 'gateway_transaction_id', 'customer_id', 'subscription_id']
	)

	# Enrich data
	for transaction in data:
		# Get customer name
		if transaction.get('customer_id'):
			customer_name = frappe.db.get_value('User', transaction['customer_id'], 'full_name')
			transaction['customer_name'] = customer_name

		# Get subscription details if available
		if transaction.get('subscription_id'):
			subscription = frappe.db.get_value(
				'SaaS Subscriptions',
				transaction['subscription_id'],
				['plan_name', 'status'],
				as_dict=True
			)
			transaction['subscription_details'] = subscription

	# Prepare response
	response = ResponseFormatter.paginated(
		data=data,
		total=total,
		page=pagination.page,
		limit=pagination.limit,
		message="Transactions retrieved successfully"
	)

	# Cache the response for 1 minute
	RedisCacheService.set(cache_key, response, expires_in_sec=60)

	return response


@frappe.whitelist()
@handle_exceptions
def get_my_transactions(page=1, limit=10, sort=None, order=None, status=None, subscription_id=None):
	"""
	Get current user's payment transactions

	Args:
		page: Page number
		limit: Items per page
		sort: Sort field
		order: Sort order
		status: Filter by status
		subscription_id: Filter by subscription

	Returns:
		Paginated list of user's transactions
	"""
	return get_transactions(
		page=page,
		limit=limit,
		sort=sort,
		order=order,
		status=status,
		customer_id=frappe.session.user,
		subscription_id=subscription_id
	)


@frappe.whitelist()
@handle_exceptions
def get_transaction(transaction_id):
	"""
	Get transaction details by ID

	Args:
		transaction_id: Transaction document name

	Returns:
		Transaction details
	"""
	# Get transaction
	transaction = BaseDataService.get_single_doc('SaaS Payment Transaction', transaction_id)

	if not transaction:
		return ResponseFormatter.not_found("Transaction not found")

	# Check permission
	if transaction['customer_id'] != frappe.session.user and not frappe.has_permission('SaaS Payment Transaction', 'read'):
		return ResponseFormatter.forbidden("You don't have permission to view this transaction")

	# Enrich with customer details
	if transaction.get('customer_id'):
		customer = frappe.db.get_value(
			'User',
			transaction['customer_id'],
			['full_name', 'email'],
			as_dict=True
		)
		transaction['customer_details'] = customer

	# Enrich with subscription details
	if transaction.get('subscription_id'):
		subscription = frappe.db.get_value(
			'SaaS Subscriptions',
			transaction['subscription_id'],
			['plan_name', 'status', 'start_date', 'end_date'],
			as_dict=True
		)
		transaction['subscription_details'] = subscription

	return ResponseFormatter.success(
		data=transaction,
		message="Transaction retrieved successfully"
	)


@frappe.whitelist()
@handle_exceptions
def get_transaction_stats(customer_id=None, subscription_id=None):
	"""
	Get transaction statistics

	Args:
		customer_id: Customer ID (optional)
		subscription_id: Subscription ID (optional)

	Returns:
		Transaction statistics
	"""
	# Build base filters
	filters = []

	# Check permissions
	if not customer_id or not frappe.has_permission('SaaS Payment Transaction', 'read'):
		customer_id = frappe.session.user

	filters.append(['customer_id', '=', customer_id])

	if subscription_id:
		filters.append(['subscription_id', '=', subscription_id])

	# Get statistics
	stats = {
		'total': BaseDataService.count_records('SaaS Payment Transaction', filters),
		'completed': BaseDataService.count_records('SaaS Payment Transaction', filters + [['status', '=', 'Completed']]),
		'failed': BaseDataService.count_records('SaaS Payment Transaction', filters + [['status', '=', 'Failed']]),
		'cancelled': BaseDataService.count_records('SaaS Payment Transaction', filters + [['status', '=', 'Cancelled']]),
		'pending': BaseDataService.count_records('SaaS Payment Transaction', filters + [['status', 'in', ['Pending', 'Initiated', 'Processing']]]),
		'refunded': BaseDataService.count_records('SaaS Payment Transaction', filters + [['status', 'in', ['Refunded', 'Partially Refunded']]])
	}

	# Get total amount paid
	total_paid = frappe.db.sql("""
		SELECT SUM(amount) as total
		FROM `tabSaaS Payment Transaction`
		WHERE customer_id = %s
		AND status = 'Completed'
		{subscription_filter}
	""".format(
		subscription_filter=f"AND subscription_id = '{subscription_id}'" if subscription_id else ""
	), (customer_id,), as_dict=True)

	stats['total_amount_paid'] = total_paid[0]['total'] if total_paid and total_paid[0]['total'] else 0

	return ResponseFormatter.success(
		data=stats,
		message="Transaction statistics retrieved successfully"
	)


@frappe.whitelist()
@handle_exceptions
def get_subscription_transactions(subscription_id, page=1, limit=10):
	"""
	Get all transactions for a specific subscription

	Args:
		subscription_id: Subscription ID
		page: Page number
		limit: Items per page

	Returns:
		Paginated list of subscription transactions
	"""
	# Check if subscription exists
	if not frappe.db.exists('SaaS Subscriptions', subscription_id):
		return ResponseFormatter.not_found("Subscription not found")

	# Check permission
	subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)
	if subscription.customer_id != frappe.session.user and not frappe.has_permission('SaaS Subscriptions', 'read'):
		return ResponseFormatter.forbidden("You don't have permission to view this subscription's transactions")

	return get_transactions(
		page=page,
		limit=limit,
		subscription_id=subscription_id,
		customer_id=subscription.customer_id
	)
