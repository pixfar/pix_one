import frappe
from frappe import _
from sslcommerz_lib import SSLCOMMERZ
import json
from datetime import datetime, timedelta
from frappe.utils import add_days, nowdate, getdate
import uuid


@frappe.whitelist(allow_guest=True)
def payment_success():
	"""
	Handle successful payment callback from SSLCommerz

	This webhook is called by SSLCommerz when payment is successful
	"""
	try:
		# Get payment response data
		payment_data = frappe.local.form_dict

		# Parse payment data if string
		if isinstance(payment_data, str):
			payment_data = json.loads(payment_data)

		# Extract important fields
		tran_id = payment_data.get('tran_id')
		val_id = payment_data.get('val_id')
		amount = payment_data.get('amount')
		card_type = payment_data.get('card_type')
		store_amount = payment_data.get('store_amount')
		card_no = payment_data.get('card_no')
		bank_tran_id = payment_data.get('bank_tran_id')
		status = payment_data.get('status')
		tran_date = payment_data.get('tran_date')
		currency = payment_data.get('currency')
		card_issuer = payment_data.get('card_issuer')
		card_brand = payment_data.get('card_brand')
		card_issuer_country = payment_data.get('card_issuer_country')
		card_issuer_country_code = payment_data.get('card_issuer_country_code')
		verify_sign = payment_data.get('verify_sign')
		verify_key = payment_data.get('verify_key')
		risk_level = payment_data.get('risk_level')
		risk_title = payment_data.get('risk_title')

		# Get value fields from payment data (custom fields passed during init)
		subscription_id = payment_data.get('value_a')  # Subscription ID
		plan_name = payment_data.get('value_b')  # Plan Name
		customer_id = payment_data.get('value_c')  # Customer ID

		# Validate transaction with SSLCommerz
		settings = get_sslcommerz_settings()
		sslcz = SSLCOMMERZ(settings)

		# Validate the transaction
		validation_response = sslcz.validationTransactionOrder(val_id)

		if validation_response.get('status') != 'VALID' and validation_response.get('status') != 'VALIDATED':
			frappe.log_error(
				f"Payment validation failed for {tran_id}: {validation_response}",
				"SSLCommerz Payment Validation Failed"
			)
			return {
				'status': 'failed',
				'message': 'Payment validation failed',
				'redirect_url': get_failure_redirect_url(tran_id, 'Validation failed')
			}

		# Create payment transaction record
		payment_transaction = create_payment_transaction(
			tran_id=tran_id,
			subscription_id=subscription_id,
			customer_id=customer_id,
			amount=amount,
			currency=currency,
			payment_method=card_type,
			gateway_transaction_id=bank_tran_id,
			gateway_response=json.dumps(payment_data, indent=2),
			gateway_status=status,
			transaction_type='Initial Payment' if not subscription_id else 'Recurring Payment'
		)

		# If subscription_id is provided, update the subscription
		if subscription_id:
			update_subscription_after_payment(
				subscription_id=subscription_id,
				payment_transaction=payment_transaction,
				amount=amount
			)
		else:
			# Create new subscription if subscription_id not provided
			# This means it's a new subscription purchase
			if plan_name and customer_id:
				subscription_id = create_new_subscription(
					plan_name=plan_name,
					customer_id=customer_id,
					payment_transaction=payment_transaction
				)

		frappe.db.commit()

		# Return success response with redirect URL
		return {
			'status': 'success',
			'message': 'Payment completed successfully',
			'transaction_id': tran_id,
			'subscription_id': subscription_id,
			'redirect_url': get_success_redirect_url(subscription_id)
		}

	except Exception as e:
		frappe.log_error(
			f"Payment Success Handler Error: {str(e)}\n{frappe.get_traceback()}",
			"Payment Success Handler"
		)
		return {
			'status': 'error',
			'message': str(e),
			'redirect_url': get_failure_redirect_url(payment_data.get('tran_id'), str(e))
		}


def get_sslcommerz_settings():
	"""Get SSLCommerz configuration"""
	sslcommerz_settings = frappe.get_doc('PixOne System Settings')
	return {
		'store_id': sslcommerz_settings.ssl_store_id,
		'store_pass': sslcommerz_settings.ssl_store_password,
		'issandbox': sslcommerz_settings.is_sandbox
	}


def create_payment_transaction(tran_id, subscription_id, customer_id, amount, currency,
							   payment_method, gateway_transaction_id, gateway_response,
							   gateway_status, transaction_type='Initial Payment'):
	"""Create a payment transaction record"""
	try:
		# Check if transaction already exists by tran_id
		existing_by_tran_id = frappe.db.exists('SaaS Payment Transaction', {'transaction_id': tran_id})
		if existing_by_tran_id:
			doc = frappe.get_doc('SaaS Payment Transaction', existing_by_tran_id)
			doc.status = 'Completed'
			doc.payment_method = payment_method
			doc.gateway_transaction_id = gateway_transaction_id
			doc.gateway_status = gateway_status
			doc.gateway_response = gateway_response
			doc.payment_date = nowdate()
			doc.save(ignore_permissions=True)
			return doc

		# Check if transaction already exists by gateway_transaction_id
		existing = frappe.db.exists('SaaS Payment Transaction', {'gateway_transaction_id': gateway_transaction_id})
		if existing:
			doc = frappe.get_doc('SaaS Payment Transaction', existing)
			doc.status = 'Completed'
			doc.gateway_status = gateway_status
			doc.gateway_response = gateway_response
			doc.save(ignore_permissions=True)
			return doc

		# Create new transaction
		payment_transaction = frappe.get_doc({
			'doctype': 'SaaS Payment Transaction',
			'transaction_id': tran_id,
			'subscription_id': subscription_id,
			'customer_id': customer_id,
			'amount': float(amount),
			'currency': currency,
			'payment_date': nowdate(),
			'payment_method': payment_method,
			'payment_gateway': 'SSLCommerz',
			'status': 'Completed',
			'transaction_type': transaction_type,
			'gateway_transaction_id': gateway_transaction_id,
			'gateway_response': gateway_response,
			'gateway_status': gateway_status,
			'is_recurring': False
		})

		payment_transaction.insert(ignore_permissions=True)
		return payment_transaction

	except Exception as e:
		frappe.log_error(f"Failed to create payment transaction: {str(e)}", "Payment Transaction Creation")
		raise


def update_subscription_after_payment(subscription_id, payment_transaction, amount):
	"""Update subscription after successful payment"""
	try:
		subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

		# Update subscription status
		if subscription.status in ['Draft', 'Pending Payment', 'Past Due']:
			subscription.status = 'Active'

		# Update payment tracking
		subscription.total_amount_paid = (subscription.total_amount_paid or 0) + float(amount)
		subscription.last_payment_amount = float(amount)
		subscription.last_payment_date = nowdate()

		# If this is initial payment, activate the subscription
		if not subscription.start_date or subscription.start_date == nowdate():
			subscription.start_date = nowdate()

			# Calculate end date based on billing interval
			end_date = calculate_subscription_end_date(
				subscription.start_date,
				subscription.billing_interval
			)
			subscription.end_date = end_date
			subscription.next_billing_date = end_date if subscription.auto_renew else None
		else:
			# For recurring payments, extend subscription
			end_date = calculate_subscription_end_date(
				subscription.end_date,
				subscription.billing_interval
			)
			subscription.end_date = end_date
			subscription.next_billing_date = end_date if subscription.auto_renew else None

		# Generate license key if not exists
		if not subscription.license_key:
			subscription.license_key = generate_license_key()

			# Create license validation record
			create_license_validation(subscription)

		subscription.save(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Failed to update subscription: {str(e)}", "Subscription Update")
		raise


def create_new_subscription(plan_name, customer_id, payment_transaction):
	"""Create a new subscription after successful payment"""
	try:
		# Get plan details
		plan = frappe.get_doc('SaaS Subscription Plan', plan_name)

		# Calculate dates
		start_date = nowdate()

		# Check if trial is applicable
		trial_ends_on = None
		if plan.allow_trial and plan.trial_period_days:
			trial_ends_on = add_days(start_date, plan.trial_period_days)

		# Calculate end date
		end_date = calculate_subscription_end_date(start_date, plan.billing_interval)

		# Create subscription
		subscription = frappe.get_doc({
			'doctype': 'SaaS Subscriptions',
			'customer_id': customer_id,
			'plan_name': plan_name,
			'app_name': 'Pix One',  # Default app name
			'status': 'Active',
			'start_date': start_date,
			'end_date': end_date,
			'trial_ends_on': trial_ends_on,
			'billing_interval': plan.billing_interval,
			'price': plan.price,
			'setup_fee': plan.setup_fee,
			'auto_renew': True,
			'next_billing_date': end_date,
			'total_amount_paid': payment_transaction.amount,
			'last_payment_amount': payment_transaction.amount,
			'last_payment_date': nowdate(),
			'license_key': generate_license_key(),
			'created_by': customer_id,
			'creation_date': datetime.now()
		})

		subscription.insert(ignore_permissions=True)

		# Update payment transaction with subscription_id
		payment_transaction.subscription_id = subscription.name
		payment_transaction.save(ignore_permissions=True)

		# Create license validation record
		create_license_validation(subscription)

		return subscription.name

	except Exception as e:
		frappe.log_error(f"Failed to create subscription: {str(e)}", "Subscription Creation")
		raise


def create_license_validation(subscription):
	"""Create license validation record for the subscription"""
	try:
		# Get plan details for limits
		plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)

		validation = frappe.get_doc({
			'doctype': 'SaaS App Validation',
			'license_key': subscription.license_key,
			'subscription_id': subscription.name,
			'customer_id': subscription.customer_id,
			'validation_status': 'Active',
			'license_issue_date': subscription.start_date,
			'license_expiry_date': subscription.end_date if subscription.billing_interval != 'Lifetime' else None,
			'is_lifetime': 1 if subscription.billing_interval == 'Lifetime' else 0,
			'max_users': plan.max_users,
			'current_users': 0,
			'max_storage_mb': plan.max_storage_mb,
			'current_storage_mb': 0,
			'max_companies': plan.max_companies,
			'current_companies': 0,
			'api_calls_per_hour': plan.api_calls_per_hour,
			'instance_url': subscription.instance_url,
			'last_validation_check': datetime.now(),
			'validation_attempts': 0,
			'access_count': 0,
			'violation_count': 0
		})

		validation.insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Failed to create license validation: {str(e)}", "License Validation Creation")
		# Don't raise - this is not critical for payment success


def calculate_subscription_end_date(start_date, billing_interval):
	"""Calculate subscription end date based on billing interval"""
	from frappe.utils import add_months, add_years, getdate

	start = getdate(start_date)

	if billing_interval == 'Monthly':
		return add_months(start, 1)
	elif billing_interval == 'Quarterly':
		return add_months(start, 3)
	elif billing_interval == 'Yearly':
		return add_years(start, 1)
	elif billing_interval == 'Lifetime':
		return add_years(start, 100)  # Set far future date
	else:
		return add_months(start, 1)  # Default to monthly


def generate_license_key():
	"""Generate a unique license key"""
	return f"LIC-{uuid.uuid4().hex[:16].upper()}"


def get_success_redirect_url(subscription_id):
	"""Get redirect URL for successful payment"""
	site_url = frappe.utils.get_url()
	if subscription_id:
		return f"{site_url}/pixone/payment/success?subscription={subscription_id}"
	return f"{site_url}/pixone/payment/success"


def get_failure_redirect_url(tran_id, reason):
	"""Get redirect URL for failed payment"""
	site_url = frappe.utils.get_url()
	return f"{site_url}/pixone/payment/failed?transaction={tran_id}&reason={reason}"
