import frappe
from frappe import _
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions
from datetime import datetime
import json


@frappe.whitelist(allow_guest=True)
@handle_exceptions
def validate_license(license_key, instance_url=None, instance_id=None, server_info=None):
	"""
	Validate a license key

	Args:
		license_key: License key to validate
		instance_url: Instance URL making the request
		instance_id: Unique instance identifier
		server_info: Server information (JSON)

	Returns:
		License validation status and details
	"""
	# Check if license exists
	if not frappe.db.exists('SaaS App Validation', license_key):
		return ResponseFormatter.not_found("Invalid license key")

	# Get license validation record
	license_validation = frappe.get_doc('SaaS App Validation', license_key)

	# Validate the license
	is_valid = license_validation.validate_license()

	if not is_valid:
		return ResponseFormatter.validation_error(
			f"License validation failed: {license_validation.validation_status}",
			details={
				'status': license_validation.validation_status,
				'reason': get_validation_failure_reason(license_validation)
			}
		)

	# Update instance information if provided
	if instance_url:
		license_validation.instance_url = instance_url
	if instance_id:
		license_validation.instance_id = instance_id
	if server_info:
		license_validation.server_info = server_info if isinstance(server_info, str) else json.dumps(server_info, indent=2)

	license_validation.save(ignore_permissions=True)

	# Get subscription details
	subscription = frappe.get_doc('SaaS Subscriptions', license_validation.subscription_id)

	# Get plan details
	plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)

	# Check resource limits
	limits_ok = license_validation.check_resource_limits()

	# Prepare response
	validation_data = {
		'license_key': license_key,
		'is_valid': True,
		'validation_status': license_validation.validation_status,
		'subscription': {
			'subscription_id': subscription.name,
			'status': subscription.status,
			'start_date': subscription.start_date,
			'end_date': subscription.end_date,
			'billing_interval': subscription.billing_interval,
			'auto_renew': subscription.auto_renew
		},
		'plan': {
			'plan_name': plan.plan_name,
			'plan_code': plan.plan_code,
			'app_name': plan.app_name
		},
		'limits': {
			'max_users': license_validation.max_users,
			'current_users': license_validation.current_users,
			'max_storage_mb': license_validation.max_storage_mb,
			'current_storage_mb': license_validation.current_storage_mb,
			'max_companies': license_validation.max_companies,
			'current_companies': license_validation.current_companies,
			'api_calls_per_hour': license_validation.api_calls_per_hour
		},
		'limits_ok': limits_ok,
		'features': [f.as_dict() for f in plan.features] if plan.features else [],
		'validation_info': {
			'last_validation_check': license_validation.last_validation_check,
			'access_count': license_validation.access_count,
			'violation_count': license_validation.violation_count
		}
	}

	frappe.db.commit()

	return ResponseFormatter.success(
		data=validation_data,
		message="License validated successfully"
	)


@frappe.whitelist(allow_guest=True)
@handle_exceptions
def check_license_status(license_key):
	"""
	Quick check of license status without full validation

	Args:
		license_key: License key to check

	Returns:
		Basic license status
	"""
	# Check if license exists
	if not frappe.db.exists('SaaS App Validation', license_key):
		return ResponseFormatter.not_found("Invalid license key")

	# Get basic license info
	license_info = frappe.db.get_value(
		'SaaS App Validation',
		license_key,
		['validation_status', 'license_expiry_date', 'is_lifetime', 'subscription_id'],
		as_dict=True
	)

	# Get subscription status
	subscription_status = frappe.db.get_value('SaaS Subscriptions', license_info['subscription_id'], 'status')

	# Check if expired
	is_expired = False
	if not license_info['is_lifetime'] and license_info['license_expiry_date']:
		from frappe.utils import getdate, nowdate
		if getdate(license_info['license_expiry_date']) < getdate(nowdate()):
			is_expired = True

	return ResponseFormatter.success(
		data={
			'license_key': license_key,
			'validation_status': license_info['validation_status'],
			'is_active': license_info['validation_status'] == 'Active' and not is_expired,
			'is_expired': is_expired,
			'is_lifetime': license_info['is_lifetime'],
			'expiry_date': license_info['license_expiry_date'],
			'subscription_status': subscription_status
		},
		message="License status retrieved successfully"
	)


@frappe.whitelist()
@handle_exceptions
def update_license_usage(license_key, current_users=None, current_storage_mb=None,
						current_companies=None, api_calls=None):
	"""
	Update license usage statistics

	Args:
		license_key: License key
		current_users: Current number of users
		current_storage_mb: Current storage usage in MB
		current_companies: Current number of companies
		api_calls: Number of API calls in current period

	Returns:
		Updated license usage
	"""
	# Check if license exists
	if not frappe.db.exists('SaaS App Validation', license_key):
		return ResponseFormatter.not_found("Invalid license key")

	license_validation = frappe.get_doc('SaaS App Validation', license_key)

	# Update usage statistics
	if current_users is not None:
		license_validation.current_users = int(current_users)

	if current_storage_mb is not None:
		license_validation.current_storage_mb = float(current_storage_mb)

	if current_companies is not None:
		license_validation.current_companies = int(current_companies)

	# Update subscription usage
	if license_validation.subscription_id:
		subscription = frappe.get_doc('SaaS Subscriptions', license_validation.subscription_id)

		if current_users is not None:
			subscription.current_users = int(current_users)

		if current_storage_mb is not None:
			subscription.current_storage_mb = float(current_storage_mb)

		if api_calls is not None:
			subscription.api_calls_this_month = int(api_calls)

		subscription.save(ignore_permissions=True)

	# Check limits
	limits_ok = license_validation.check_resource_limits()

	license_validation.save(ignore_permissions=True)
	frappe.db.commit()

	return ResponseFormatter.success(
		data={
			'license_key': license_key,
			'usage': {
				'current_users': license_validation.current_users,
				'current_storage_mb': license_validation.current_storage_mb,
				'current_companies': license_validation.current_companies
			},
			'limits': {
				'max_users': license_validation.max_users,
				'max_storage_mb': license_validation.max_storage_mb,
				'max_companies': license_validation.max_companies
			},
			'limits_ok': limits_ok,
			'violation_count': license_validation.violation_count
		},
		message="License usage updated successfully"
	)


@frappe.whitelist()
@handle_exceptions
def get_license_details(license_key):
	"""
	Get detailed license information (authenticated)

	Args:
		license_key: License key

	Returns:
		Complete license details
	"""
	# Check if license exists
	if not frappe.db.exists('SaaS App Validation', license_key):
		return ResponseFormatter.not_found("Invalid license key")

	license_validation = frappe.get_doc('SaaS App Validation', license_key)

	# Check permission
	subscription = frappe.get_doc('SaaS Subscriptions', license_validation.subscription_id)
	if subscription.customer_id != frappe.session.user and not frappe.has_permission('SaaS App Validation', 'read'):
		return ResponseFormatter.forbidden("You don't have permission to view this license")

	# Get plan details
	plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)

	return ResponseFormatter.success(
		data={
			'license': license_validation.as_dict(),
			'subscription': subscription.as_dict(),
			'plan': {
				'plan_name': plan.plan_name,
				'plan_code': plan.plan_code,
				'app_name': plan.app_name,
				'features': [f.as_dict() for f in plan.features] if plan.features else []
			}
		},
		message="License details retrieved successfully"
	)


def get_validation_failure_reason(license_validation):
	"""Get human-readable validation failure reason"""
	status = license_validation.validation_status

	if status == 'Expired':
		return f"License expired on {license_validation.license_expiry_date}"
	elif status == 'Suspended':
		return "License has been suspended"
	elif status == 'Revoked':
		return "License has been revoked"
	elif status == 'Invalid':
		return "License is invalid"
	else:
		return "License validation failed"
