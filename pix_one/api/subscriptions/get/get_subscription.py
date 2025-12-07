import frappe
from frappe import _
from pix_one.common.shared import BaseDataService
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions
from pix_one.common.cache import RedisCacheService


@frappe.whitelist()
@handle_exceptions
def get_subscription(subscription_id):
	"""
	Get subscription details by ID

	Args:
		subscription_id: Subscription document name

	Returns:
		Subscription details with enriched data
	"""
	# Check if subscription exists
	subscription = BaseDataService.get_single_doc('SaaS Subscriptions', subscription_id)

	if not subscription:
		return ResponseFormatter.not_found("Subscription not found")

	# Check permission - users can only view their own subscriptions unless admin
	if subscription['customer_id'] != frappe.session.user and not frappe.has_permission('SaaS Subscriptions', 'read'):
		return ResponseFormatter.forbidden("You don't have permission to view this subscription")

	# Enrich with plan details
	if subscription.get('plan_name'):
		plan = frappe.get_doc('SaaS Subscription Plan', subscription['plan_name'])
		subscription['plan_details'] = {
			'plan_name': plan.plan_name,
			'plan_code': plan.plan_code,
			'short_description': plan.short_description,
			'price': plan.price,
			'currency': plan.currency,
			'setup_fee': plan.setup_fee,
			'billing_interval': plan.billing_interval,
			'max_users': plan.max_users,
			'max_storage_mb': plan.max_storage_mb,
			'max_companies': plan.max_companies,
			'api_calls_per_hour': plan.api_calls_per_hour,
			'features': [f.as_dict() for f in plan.features] if plan.features else []
		}

	# Get customer details
	if subscription.get('customer_id'):
		customer = frappe.db.get_value(
			'User',
			subscription['customer_id'],
			['full_name', 'email', 'phone', 'mobile_no'],
			as_dict=True
		)
		subscription['customer_details'] = customer

	# Get license validation details if available
	if subscription.get('license_key'):
		license_validation = frappe.db.get_value(
			'SaaS App Validation',
			subscription['license_key'],
			['validation_status', 'current_users', 'current_storage_mb', 'current_companies',
			 'api_calls_per_hour', 'last_validation_check', 'access_count', 'violation_count'],
			as_dict=True
		)
		subscription['license_validation'] = license_validation

	# Get recent payment transactions
	payment_transactions = frappe.get_all(
		'SaaS Payment Transaction',
		filters={'subscription_id': subscription_id},
		fields=['name', 'transaction_id', 'amount', 'currency', 'payment_date',
				'status', 'transaction_type', 'payment_method'],
		order_by='payment_date desc',
		limit=10
	)
	subscription['recent_payments'] = payment_transactions

	# Calculate usage percentages
	if subscription.get('plan_details'):
		usage_stats = calculate_usage_stats(subscription)
		subscription['usage_stats'] = usage_stats

	# Cache the response for 1 minute
	cache_key = f"subscription:details:{subscription_id}"
	response = ResponseFormatter.success(
		data=subscription,
		message="Subscription retrieved successfully"
	)
	RedisCacheService.set(cache_key, response, expires_in_sec=60)

	return response


@frappe.whitelist()
@handle_exceptions
def get_subscription_by_license(license_key):
	"""
	Get subscription by license key

	Args:
		license_key: License key

	Returns:
		Subscription details
	"""
	# Get subscription by license key
	subscription_id = frappe.db.get_value('SaaS Subscriptions', {'license_key': license_key}, 'name')

	if not subscription_id:
		return ResponseFormatter.not_found("Subscription not found for this license key")

	return get_subscription(subscription_id)


def calculate_usage_stats(subscription):
	"""Calculate usage statistics as percentages"""
	stats = {}
	plan = subscription.get('plan_details', {})
	validation = subscription.get('license_validation', {})

	# Users usage
	if plan.get('max_users') and plan['max_users'] > 0:
		current_users = validation.get('current_users', 0)
		stats['users_percentage'] = round((current_users / plan['max_users']) * 100, 2)
		stats['users_used'] = current_users
		stats['users_limit'] = plan['max_users']

	# Storage usage
	if plan.get('max_storage_mb') and plan['max_storage_mb'] > 0:
		current_storage = validation.get('current_storage_mb', 0)
		stats['storage_percentage'] = round((current_storage / plan['max_storage_mb']) * 100, 2)
		stats['storage_used'] = current_storage
		stats['storage_limit'] = plan['max_storage_mb']

	# Companies usage
	if plan.get('max_companies') and plan['max_companies'] > 0:
		current_companies = validation.get('current_companies', 0)
		stats['companies_percentage'] = round((current_companies / plan['max_companies']) * 100, 2)
		stats['companies_used'] = current_companies
		stats['companies_limit'] = plan['max_companies']

	# Calculate days remaining
	if subscription.get('end_date'):
		from frappe.utils import getdate, date_diff, nowdate
		end_date = getdate(subscription['end_date'])
		today = getdate(nowdate())
		days_remaining = date_diff(end_date, today)
		stats['days_remaining'] = max(0, days_remaining)

	return stats
