import frappe
from frappe import _
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions
from pix_one.common.cache import RedisCacheService
from frappe.utils import nowdate


@frappe.whitelist()
@handle_exceptions
def cancel_subscription(subscription_id, reason=None, notes=None, immediate=False):
	"""
	Cancel a subscription

	Args:
		subscription_id: Subscription document name
		reason: Cancellation reason
		notes: Additional notes
		immediate: If True, cancel immediately. If False, cancel at end of billing period

	Returns:
		Cancelled subscription details
	"""
	# Check if subscription exists
	if not frappe.db.exists('SaaS Subscriptions', subscription_id):
		return ResponseFormatter.not_found("Subscription not found")

	subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

	# Check permission - users can only cancel their own subscriptions unless admin
	if subscription.customer_id != frappe.session.user and not frappe.has_permission('SaaS Subscriptions', 'write'):
		return ResponseFormatter.forbidden("You don't have permission to cancel this subscription")

	# Check if subscription is already cancelled
	if subscription.status == 'Cancelled':
		return ResponseFormatter.validation_error(
			"Subscription is already cancelled",
			details={"status": "Cancelled"}
		)

	# Update subscription
	subscription.cancellation_date = nowdate()
	subscription.cancellation_reason = reason or 'User requested cancellation'
	subscription.cancellation_notes = notes

	if immediate:
		# Cancel immediately
		subscription.status = 'Cancelled'
		subscription.auto_renew = False
		subscription.next_billing_date = None

		# Update license validation status
		if subscription.license_key:
			update_license_status(subscription.license_key, 'Revoked')

	else:
		# Cancel at end of billing period
		subscription.auto_renew = False
		subscription.next_billing_date = None
		# Status remains Active until end_date

	subscription.save()

	# Invalidate cache
	RedisCacheService.delete(f"subscription:details:{subscription_id}")
	RedisCacheService.delete_pattern(f"subscriptions:list:*")

	frappe.db.commit()

	return ResponseFormatter.success(
		data={
			'subscription': subscription.as_dict(),
			'cancelled_immediately': immediate,
			'access_until': subscription.end_date if not immediate else nowdate()
		},
		message=f"Subscription cancelled {'immediately' if immediate else 'successfully. Access will continue until end of billing period'}"
	)


@frappe.whitelist()
@handle_exceptions
def reactivate_subscription(subscription_id):
	"""
	Reactivate a cancelled subscription (only if not yet expired)

	Args:
		subscription_id: Subscription document name

	Returns:
		Reactivated subscription details
	"""
	# Check if subscription exists
	if not frappe.db.exists('SaaS Subscriptions', subscription_id):
		return ResponseFormatter.not_found("Subscription not found")

	subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

	# Check permission
	if subscription.customer_id != frappe.session.user and not frappe.has_permission('SaaS Subscriptions', 'write'):
		return ResponseFormatter.forbidden("You don't have permission to reactivate this subscription")

	# Check if subscription can be reactivated
	if subscription.status not in ['Cancelled', 'Expired']:
		return ResponseFormatter.validation_error(
			"Only cancelled or expired subscriptions can be reactivated",
			details={"status": subscription.status}
		)

	# Check if subscription has expired
	from frappe.utils import getdate, nowdate
	if subscription.end_date and getdate(subscription.end_date) < getdate(nowdate()):
		return ResponseFormatter.validation_error(
			"Cannot reactivate expired subscription. Please purchase a new subscription.",
			details={"expired_date": subscription.end_date}
		)

	# Reactivate subscription
	subscription.status = 'Active'
	subscription.auto_renew = True
	subscription.cancellation_date = None
	subscription.cancellation_reason = None
	subscription.cancellation_notes = None

	# Calculate next billing date
	if subscription.billing_interval != 'Lifetime':
		subscription.next_billing_date = subscription.end_date

	# Update license validation status
	if subscription.license_key:
		update_license_status(subscription.license_key, 'Active')

	subscription.save()

	# Invalidate cache
	RedisCacheService.delete(f"subscription:details:{subscription_id}")
	RedisCacheService.delete_pattern(f"subscriptions:list:*")

	frappe.db.commit()

	return ResponseFormatter.success(
		data=subscription.as_dict(),
		message="Subscription reactivated successfully"
	)


@frappe.whitelist()
@handle_exceptions
def suspend_subscription(subscription_id, reason=None):
	"""
	Suspend a subscription temporarily (admin only)

	Args:
		subscription_id: Subscription document name
		reason: Suspension reason

	Returns:
		Suspended subscription details
	"""
	# Check admin permission
	if not frappe.has_permission('SaaS Subscriptions', 'write'):
		return ResponseFormatter.forbidden("Only administrators can suspend subscriptions")

	# Check if subscription exists
	if not frappe.db.exists('SaaS Subscriptions', subscription_id):
		return ResponseFormatter.not_found("Subscription not found")

	subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

	# Check if subscription is active
	if subscription.status not in ['Active', 'Trial']:
		return ResponseFormatter.validation_error(
			"Only active or trial subscriptions can be suspended",
			details={"status": subscription.status}
		)

	# Suspend subscription
	subscription.status = 'Suspended'
	if not subscription.cancellation_notes:
		subscription.cancellation_notes = f"Suspended: {reason or 'Administrative action'}"

	# Update license validation status
	if subscription.license_key:
		update_license_status(subscription.license_key, 'Suspended')

	subscription.save()

	# Invalidate cache
	RedisCacheService.delete(f"subscription:details:{subscription_id}")
	RedisCacheService.delete_pattern(f"subscriptions:list:*")

	frappe.db.commit()

	return ResponseFormatter.success(
		data=subscription.as_dict(),
		message="Subscription suspended successfully"
	)


def update_license_status(license_key, status):
	"""Update license validation status"""
	try:
		if frappe.db.exists('SaaS App Validation', license_key):
			license_doc = frappe.get_doc('SaaS App Validation', license_key)
			license_doc.validation_status = status
			license_doc.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Failed to update license status: {str(e)}", "License Status Update")
