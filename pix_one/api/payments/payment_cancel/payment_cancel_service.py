import frappe
from frappe import _
import json
from frappe.utils import nowdate


@frappe.whitelist(allow_guest=True)
def payment_cancel():
	"""
	Handle cancelled payment callback from SSLCommerz

	This webhook is called by SSLCommerz when payment is cancelled by user
	"""
	try:
		# Get payment response data
		payment_data = frappe.local.form_dict

		# Parse payment data if string
		if isinstance(payment_data, str):
			payment_data = json.loads(payment_data)

		# Extract important fields
		tran_id = payment_data.get('tran_id')
		status = payment_data.get('status')
		amount = payment_data.get('amount')
		currency = payment_data.get('currency')

		# Get value fields from payment data (custom fields passed during init)
		subscription_id = payment_data.get('value_a')  # Subscription ID
		plan_name = payment_data.get('value_b')  # Plan Name
		customer_id = payment_data.get('value_c')  # Customer ID

		# Create cancelled payment transaction record
		payment_transaction = create_cancelled_payment_transaction(
			tran_id=tran_id,
			subscription_id=subscription_id,
			customer_id=customer_id,
			amount=amount,
			currency=currency,
			gateway_response=json.dumps(payment_data, indent=2),
			gateway_status=status
		)

		# Update subscription status if exists
		if subscription_id:
			update_subscription_after_cancelled_payment(subscription_id)

		frappe.db.commit()

		# Redirect to cancelled page
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = get_cancel_redirect_url(tran_id)

	except Exception as e:
		frappe.log_error(
			f"Payment Cancel Handler Error: {str(e)}\n{frappe.get_traceback()}",
			"Payment Cancel Handler"
		)
		# Redirect to cancelled page
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = get_cancel_redirect_url(payment_data.get('tran_id'))


def create_cancelled_payment_transaction(tran_id, subscription_id, customer_id, amount,
										 currency, gateway_response, gateway_status):
	"""Create a cancelled payment transaction record"""
	try:
		payment_transaction = frappe.get_doc({
			'doctype': 'SaaS Payment Transaction',
			'transaction_id': tran_id,
			'subscription_id': subscription_id,
			'customer_id': customer_id,
			'amount': float(amount) if amount else 0,
			'currency': currency or 'BDT',
			'payment_date': nowdate(),
			'payment_gateway': 'SSLCommerz',
			'status': 'Cancelled',
			'transaction_type': 'Initial Payment' if not subscription_id else 'Recurring Payment',
			'gateway_response': gateway_response,
			'gateway_status': gateway_status,
			'failure_reason': 'Payment cancelled by user',
			'is_recurring': False
		})

		payment_transaction.insert(ignore_permissions=True)
		return payment_transaction

	except Exception as e:
		frappe.log_error(f"Failed to create cancelled payment transaction: {str(e)}", "Cancelled Payment Transaction Creation")
		raise


def update_subscription_after_cancelled_payment(subscription_id):
	"""Update subscription status after cancelled payment"""
	try:
		subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

		# If subscription is in Draft or Pending Payment, keep it that way
		if subscription.status in ['Draft', 'Pending Payment']:
			subscription.status = 'Pending Payment'
			subscription.save(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Failed to update subscription after cancelled payment: {str(e)}", "Subscription Update After Cancelled Payment")
		# Don't raise - this is not critical


def get_cancel_redirect_url(tran_id):
	"""Get redirect URL for cancelled payment"""
	site_url = frappe.utils.get_url()
	return f"{site_url}/dashboard/payments/cancelled?transaction={tran_id}"
