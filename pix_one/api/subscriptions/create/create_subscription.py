import frappe
from frappe import _
from pix_one.common.interceptors import ResponseFormatter, handle_exceptions
import json


@frappe.whitelist()
@handle_exceptions
def create_subscription(plan_name, customer_id=None, app_name=None):
	"""
	Create a new subscription (draft state, pending payment)

	Args:
		plan_name: Name of the subscription plan
		customer_id: Customer user ID (optional, defaults to current user)
		app_name: App name (optional, defaults to 'Pix One')

	Returns:
		{
			"success": true,
			"data": {
				"subscription": {...},
				"payment_data": {...}  # Data needed to initiate payment
			},
			"message": "Subscription created successfully"
		}
	"""
	# Get current user if customer_id not provided
	if not customer_id:
		customer_id = frappe.session.user

	# Validate plan exists
	if not frappe.db.exists('SaaS Subscription Plan', plan_name):
		return ResponseFormatter.not_found(f"Subscription plan '{plan_name}' not found")

	# Get plan details
	plan = frappe.get_doc('SaaS Subscription Plan', plan_name)

	# Check if plan is active
	if not plan.is_active:
		return ResponseFormatter.validation_error(
			"This subscription plan is not currently available",
			details={"plan": "Plan is inactive"}
		)

	# Set default app name if not provided
	if not app_name:
		app_name = 'Pix One'

	# Check for existing active subscription
	existing_subscription = frappe.db.get_value(
		'SaaS Subscriptions',
		{
			'customer_id': customer_id,
			'plan_name': plan_name,
			'status': ['in', ['Active', 'Trial', 'Pending Payment']]
		},
		'name'
	)

	if existing_subscription:
		return ResponseFormatter.validation_error(
			"You already have an active subscription for this plan",
			details={"subscription_id": existing_subscription}
		)

	# Calculate trial end date
	trial_ends_on = None
	if plan.allow_trial and plan.trial_period_days:
		from frappe.utils import add_days, nowdate
		trial_ends_on = add_days(nowdate(), plan.trial_period_days)

	# Calculate total amount (price + setup fee)
	total_amount = (plan.price or 0) + (plan.setup_fee or 0)

	# Create subscription in Draft state
	subscription = frappe.get_doc({
		'doctype': 'SaaS Subscriptions',
		'customer_id': customer_id,
		'plan_name': plan_name,
		'app_name': app_name,
		'status': 'Pending Payment',
		'billing_interval': plan.billing_interval,
		'price': plan.price,
		'setup_fee': plan.setup_fee,
		'auto_renew': True,
		'trial_ends_on': trial_ends_on,
		'created_by': frappe.session.user,
		'creation_date': frappe.utils.now_datetime()
	})

	subscription.insert()
	frappe.db.commit()

	# Get customer details for payment
	customer = frappe.get_doc('User', customer_id)

	# Prepare payment data
	payment_data = {
		'total_amount': total_amount,
		'currency': plan.currency or 'BDT',
		'product_name': f"{plan.plan_name} Subscription",
		'product_category': 'Subscription',
		'cus_name': customer.full_name or customer.name,
		'cus_email': customer.email,
		'cus_phone': customer.phone or customer.mobile_no or '01700000000',
		'cus_add1': 'N/A',
		'cus_city': 'Dhaka',
		'cus_country': 'Bangladesh',
		'num_of_item': 1,
		'shipping_method': 'NO',
		# Custom value fields to pass subscription data
		'value_a': subscription.name,  # Subscription ID
		'value_b': plan_name,  # Plan Name
		'value_c': customer_id  # Customer ID
	}

	return ResponseFormatter.created(
		data={
			'subscription': subscription.as_dict(),
			'payment_data': payment_data,
			'total_amount': total_amount,
			'plan_details': {
				'name': plan.plan_name,
				'price': plan.price,
				'setup_fee': plan.setup_fee,
				'billing_interval': plan.billing_interval,
				'trial_period_days': plan.trial_period_days if plan.allow_trial else 0
			}
		},
		message="Subscription created successfully. Please proceed with payment."
	)


@frappe.whitelist()
@handle_exceptions
def initiate_subscription_payment(subscription_id):
	"""
	Initiate payment for an existing subscription

	Args:
		subscription_id: Subscription document name

	Returns:
		Payment initiation data
	"""
	# Get subscription
	if not frappe.db.exists('SaaS Subscriptions', subscription_id):
		return ResponseFormatter.not_found("Subscription not found")

	subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

	# Check if user has permission
	if subscription.customer_id != frappe.session.user and not frappe.has_permission('SaaS Subscriptions', 'write'):
		return ResponseFormatter.forbidden("You don't have permission to access this subscription")

	# Check subscription status
	if subscription.status not in ['Draft', 'Pending Payment', 'Past Due']:
		return ResponseFormatter.validation_error(
			"Subscription is not in a state that requires payment",
			details={"status": subscription.status}
		)

	# Get plan details
	plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)

	# Calculate amount (for renewals, only plan price)
	if subscription.status == 'Past Due':
		total_amount = plan.price
	else:
		total_amount = (plan.price or 0) + (subscription.setup_fee or 0)

	# Get customer details
	customer = frappe.get_doc('User', subscription.customer_id)

	# Prepare payment data
	payment_data = {
		'total_amount': total_amount,
		'currency': plan.currency or 'BDT',
		'product_name': f"{plan.plan_name} Subscription",
		'product_category': 'Subscription',
		'cus_name': customer.full_name or customer.name,
		'cus_email': customer.email,
		'cus_phone': customer.phone or customer.mobile_no or '01700000000',
		'cus_add1': 'N/A',
		'cus_city': 'Dhaka',
		'cus_country': 'Bangladesh',
		'num_of_item': 1,
		'shipping_method': 'NO',
		# Custom value fields
		'value_a': subscription.name,
		'value_b': subscription.plan_name,
		'value_c': subscription.customer_id
	}

	return ResponseFormatter.success(
		data={
			'subscription_id': subscription.name,
			'payment_data': payment_data,
			'total_amount': total_amount
		},
		message="Payment data prepared successfully"
	)
