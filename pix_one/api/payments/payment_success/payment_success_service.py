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
		plan_name = payment_data.get('value_a')  # Plan ID/Name
		plan_code = payment_data.get('value_b')  # Plan Code
		customer_id = payment_data.get('value_c')  # Customer Email/ID

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

		# Create/update payment transaction record
		payment_transaction = create_payment_transaction(
			tran_id=tran_id,
			subscription_id=None,  # Will be set from existing transaction if found
			customer_id=customer_id,
			amount=amount,
			currency=currency,
			payment_method=card_type,
			gateway_transaction_id=bank_tran_id,
			gateway_response=json.dumps(payment_data, indent=2),
			gateway_status=status,
			transaction_type='Initial Payment'
		)

		# Get subscription_id from the payment transaction (created during init_payment)
		subscription_id = payment_transaction.subscription_id

		# If subscription_id exists, update the subscription
		if subscription_id:
			update_subscription_after_payment(
				subscription_id=subscription_id,
				payment_transaction=payment_transaction,
				amount=amount
			)
		else:
			# Create new subscription if subscription_id not found
			# This handles edge cases where subscription wasn't created during init
			if plan_name and customer_id:
				subscription_id = create_new_subscription(
					plan_name=plan_name,
					customer_id=customer_id,
					payment_transaction=payment_transaction
				)

		frappe.db.commit()

		# Redirect to success page
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = get_success_redirect_url(subscription_id)

	except Exception as e:
		frappe.log_error(
			f"Payment Success Handler Error: {str(e)}\n{frappe.get_traceback()}",
			"Payment Success Handler"
		)
		# Redirect to failure page
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = get_failure_redirect_url(payment_data.get('tran_id'), str(e))


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
		# Normalize payment method to match allowed values
		normalized_payment_method = normalize_payment_method(payment_method)

		# Check if transaction already exists by tran_id
		existing_by_tran_id = frappe.db.exists('SaaS Payment Transaction', {'transaction_id': tran_id})
		if existing_by_tran_id:
			doc = frappe.get_doc('SaaS Payment Transaction', existing_by_tran_id)
			doc.status = 'Completed'
			doc.payment_method = normalized_payment_method
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
			doc.payment_method = normalized_payment_method
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
			'payment_method': normalized_payment_method,
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


def normalize_payment_method(payment_method):
	"""
	Normalize payment method from gateway to match SaaS Payment Transaction allowed values
	Allowed: Credit Card, Debit Card, Mobile Banking, Internet Banking, Bank Transfer, Cash
	"""
	if not payment_method:
		return "Mobile Banking"  # Default

	payment_method_upper = payment_method.upper()

	# Map common payment method variations to allowed values
	if any(x in payment_method_upper for x in ['BKASH', 'NAGAD', 'ROCKET', 'UPAY', 'MOBILE']):
		return "Mobile Banking"
	elif any(x in payment_method_upper for x in ['VISA', 'MASTER', 'AMEX', 'CREDIT']):
		return "Credit Card"
	elif 'DEBIT' in payment_method_upper:
		return "Debit Card"
	elif any(x in payment_method_upper for x in ['INTERNET', 'ONLINE', 'NET']):
		return "Internet Banking"
	elif any(x in payment_method_upper for x in ['BANK', 'TRANSFER', 'NEFT', 'RTGS']):
		return "Bank Transfer"
	elif 'CASH' in payment_method_upper:
		return "Cash"
	else:
		# Default to Mobile Banking for unknown methods
		return "Mobile Banking"


def update_subscription_after_payment(subscription_id, payment_transaction, amount):
	"""Update subscription after successful payment"""
	try:
		frappe.logger().info(f"Updating subscription {subscription_id} after payment")
		subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)
		plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)

		frappe.logger().info(f"Current subscription status: {subscription.status}, docstatus: {subscription.docstatus}")

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

		# Save subscription first
		subscription.save(ignore_permissions=True)
		frappe.logger().info(f"Subscription saved. Status: {subscription.status}, docstatus: {subscription.docstatus}")

		# Submit the subscription if still in draft
		if subscription.docstatus == 0:
			subscription.submit()
			frappe.logger().info(f"Subscription submitted. New docstatus: {subscription.docstatus}")

		# Create license validation record after submission
		if not frappe.db.exists("SaaS App Validation", subscription.license_key):
			frappe.logger().info(f"Creating license validation for {subscription.license_key}")
			create_license_validation(subscription, plan)
		else:
			frappe.logger().info(f"License validation already exists for {subscription.license_key}")

		# Create Sales Invoice and Payment Entry
		try:
			frappe.logger().info(f"Creating sales invoice for subscription {subscription.name}")
			create_sales_invoice_and_payment(subscription, plan, payment_transaction, amount)
		except Exception as e:
			frappe.log_error(
				f"Failed to create sales invoice: {str(e)}\n{frappe.get_traceback()}",
				"Sales Invoice Creation Error"
			)
			# Don't raise - subscription is updated, invoice can be created manually

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			f"Failed to update subscription: {str(e)}\n{frappe.get_traceback()}",
			"Subscription Update Error"
		)
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


def create_license_validation(subscription, plan=None):
	"""Create license validation record for the subscription"""
	try:
		# Get plan details for limits if not provided
		if not plan:
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
		return f"{site_url}/dashboard/payments/success?subscription={subscription_id}"
	return f"{site_url}/dashboard/payments/success"


def get_failure_redirect_url(tran_id, reason):
	"""Get redirect URL for failed payment"""
	site_url = frappe.utils.get_url()
	return f"{site_url}/dashboard/payments/failed?transaction={tran_id}&reason={reason}"


def create_sales_invoice_and_payment(subscription, plan, payment_transaction, amount):
	"""
	Create Sales Invoice and Payment Entry for subscription payment

	Args:
		subscription: SaaS Subscriptions document
		plan: SaaS Subscription Plan document
		payment_transaction: SaaS Payment Transaction document
		amount: Payment amount
	"""
	# Save current user context
	current_user = frappe.session.user

	try:
		# Switch to Administrator context to avoid permission issues
		# This is necessary because payment_success endpoint is guest-allowed
		frappe.set_user("Administrator")

		# Get or create customer
		customer = get_or_create_customer_for_invoice(subscription.customer_id)

		# Get or create item
		item_code = get_or_create_item_for_plan(plan)

		# Get default company
		company = frappe.defaults.get_defaults().get("company") or frappe.db.get_single_value("Global Defaults", "default_company")

		if not company:
			frappe.throw(_("Please set a default company in Global Defaults"))

		# Create Sales Invoice
		sales_invoice = frappe.get_doc({
			"doctype": "Sales Invoice",
			"customer": customer,
			"posting_date": payment_transaction.payment_date,
			"due_date": payment_transaction.payment_date,
			"company": company,
			"currency": payment_transaction.currency or plan.currency,
			"remarks": f"Subscription: {subscription.name} - Plan: {plan.plan_name}",
		})

		# Add plan price as line item
		sales_invoice.append("items", {
			"item_code": item_code,
			"item_name": plan.plan_name,
			"description": plan.short_description or plan.plan_name,
			"qty": 1,
			"rate": plan.price,
			"amount": plan.price,
		})

		# Add setup fee if applicable and it's initial payment
		if payment_transaction.transaction_type == "Initial Payment" and plan.setup_fee > 0:
			sales_invoice.append("items", {
				"item_code": item_code,
				"item_name": f"{plan.plan_name} - Setup Fee",
				"description": "One-time setup fee",
				"qty": 1,
				"rate": plan.setup_fee,
				"amount": plan.setup_fee,
			})

		# Insert and submit
		sales_invoice.insert(ignore_permissions=True)
		sales_invoice.submit()

		frappe.logger().info(f"Sales invoice {sales_invoice.name} created and submitted")

		# Update payment transaction with invoice number
		payment_transaction.invoice_number = sales_invoice.name
		payment_transaction.save(ignore_permissions=True)

		# Create Payment Entry
		try:
			create_payment_entry_for_invoice(customer, sales_invoice, payment_transaction, amount)
		except Exception as e:
			frappe.log_error(
				f"Failed to create payment entry for {sales_invoice.name}: {str(e)}\n{frappe.get_traceback()}",
				"Payment Entry Creation"
			)
			# Don't raise - invoice is created, payment entry can be created manually

		return sales_invoice

	finally:
		# Restore original user context
		frappe.set_user(current_user)


def get_or_create_customer_for_invoice(user_email):
	"""Get existing customer or return user email"""
	# Try to find customer by email
	customer = frappe.db.get_value("Customer", {"email_id": user_email}, "name")

	if customer:
		return customer

	# Return user email as fallback
	return user_email


def get_or_create_item_for_plan(plan):
	"""Get or create item for subscription plan"""
	item_code = plan.plan_code

	# Check if item exists
	if frappe.db.exists("Item", item_code):
		return item_code

	# Create item
	item_group = frappe.db.get_single_value("Stock Settings", "item_group") or "Products"

	description = f"<p>{plan.short_description or plan.plan_name}</p>"
	description += f"<p><strong>Billing Interval:</strong> {plan.billing_interval}</p>"

	if plan.max_users:
		description += f"<p><strong>Max Users:</strong> {plan.max_users}</p>"
	if plan.max_storage_mb:
		description += f"<p><strong>Max Storage:</strong> {plan.max_storage_mb} MB</p>"

	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": item_code,
		"item_name": plan.plan_name,
		"item_group": item_group,
		"stock_uom": "Nos",
		"is_stock_item": 0,
		"is_sales_item": 1,
		"is_purchase_item": 0,
		"description": description,
		"standard_rate": plan.price,
		"disabled": 0 if plan.is_active else 1,
	})

	item.insert(ignore_permissions=True)

	# Create Item Price
	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"

	item_price = frappe.get_doc({
		"doctype": "Item Price",
		"item_code": item_code,
		"price_list": price_list,
		"currency": plan.currency,
		"price_list_rate": plan.price,
	})

	item_price.insert(ignore_permissions=True)

	return item_code


def create_payment_entry_for_invoice(customer, sales_invoice, payment_transaction, amount):
	"""Create payment entry against sales invoice"""
	try:
		company = sales_invoice.company

		# Get default cash/bank account
		mode_of_payment = frappe.db.get_value("Mode of Payment", {"type": "Bank"}, "name") or "Cash"
		default_account = frappe.db.get_value(
			"Mode of Payment Account",
			{"parent": mode_of_payment, "company": company},
			"default_account"
		)

		if not default_account:
			# Get default cash account
			default_account = frappe.db.get_value("Account", {
				"company": company,
				"account_type": "Cash",
				"is_group": 0
			}, "name")

		if not default_account:
			frappe.log_error(
				f"No default payment account found for company {company}",
				"Payment Entry Creation Failed"
			)
			return None

		# Create payment entry
		payment_entry = frappe.get_doc({
			"doctype": "Payment Entry",
			"payment_type": "Receive",
			"posting_date": payment_transaction.payment_date,
			"mode_of_payment": mode_of_payment,
			"party_type": "Customer",
			"party": customer,
			"paid_to": default_account,
			"paid_amount": float(amount),
			"received_amount": float(amount),
			"reference_no": payment_transaction.gateway_transaction_id or payment_transaction.transaction_id,
			"reference_date": payment_transaction.payment_date,
			"company": company,
			"remarks": f"Payment for {sales_invoice.name}",
		})

		# Add reference to sales invoice
		payment_entry.append("references", {
			"reference_doctype": "Sales Invoice",
			"reference_name": sales_invoice.name,
			"allocated_amount": float(amount),
		})

		payment_entry.insert(ignore_permissions=True)
		payment_entry.submit()

		frappe.logger().info(f"Payment entry {payment_entry.name} created and submitted for {sales_invoice.name}")

		return payment_entry

	except Exception as e:
		frappe.log_error(
			f"Error creating payment entry: {frappe.get_traceback()}",
			f"Payment Entry Error for {sales_invoice.name}"
		)
		return None
