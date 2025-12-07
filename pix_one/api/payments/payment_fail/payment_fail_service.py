import frappe
from frappe import _
import json
from frappe.utils import nowdate


@frappe.whitelist(allow_guest=True)
def payment_fail():
	"""
	Handle failed payment callback from SSLCommerz

	This webhook is called by SSLCommerz when payment fails
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
		error = payment_data.get('error')
		amount = payment_data.get('amount')
		currency = payment_data.get('currency')

		# Get value fields from payment data (custom fields passed during init)
		subscription_id = payment_data.get('value_a')  # Subscription ID
		plan_name = payment_data.get('value_b')  # Plan Name
		customer_id = payment_data.get('value_c')  # Customer ID

		# Create failed payment transaction record
		payment_transaction = create_failed_payment_transaction(
			tran_id=tran_id,
			subscription_id=subscription_id,
			customer_id=customer_id,
			amount=amount,
			currency=currency,
			failure_reason=error or 'Payment failed',
			gateway_response=json.dumps(payment_data, indent=2),
			gateway_status=status
		)

		# Update subscription status if exists
		if subscription_id:
			update_subscription_after_failed_payment(subscription_id)

		frappe.db.commit()

		# Return failure response with redirect URL
		return {
			'status': 'failed',
			'message': error or 'Payment failed',
			'transaction_id': tran_id,
			'redirect_url': get_failure_redirect_url(tran_id, error or 'Payment failed')
		}

	except Exception as e:
		frappe.log_error(
			f"Payment Fail Handler Error: {str(e)}\n{frappe.get_traceback()}",
			"Payment Fail Handler"
		)
		return {
			'status': 'error',
			'message': str(e),
			'redirect_url': get_failure_redirect_url(payment_data.get('tran_id'), str(e))
		}


def create_failed_payment_transaction(tran_id, subscription_id, customer_id, amount,
									  currency, failure_reason, gateway_response, gateway_status):
	"""Create a failed payment transaction record"""
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
			'status': 'Failed',
			'transaction_type': 'Initial Payment' if not subscription_id else 'Recurring Payment',
			'gateway_response': gateway_response,
			'gateway_status': gateway_status,
			'failure_reason': failure_reason,
			'is_recurring': False
		})

		payment_transaction.insert(ignore_permissions=True)
		return payment_transaction

	except Exception as e:
		frappe.log_error(f"Failed to create failed payment transaction: {str(e)}", "Failed Payment Transaction Creation")
		raise


def update_subscription_after_failed_payment(subscription_id):
	"""Update subscription status after failed payment"""
	try:
		subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

		# Update subscription status to Past Due if it was active
		if subscription.status == 'Active':
			subscription.status = 'Past Due'
		elif subscription.status in ['Draft', 'Pending Payment']:
			# Keep it in pending state
			subscription.status = 'Pending Payment'

		subscription.save(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(f"Failed to update subscription after failed payment: {str(e)}", "Subscription Update After Failed Payment")
		# Don't raise - this is not critical


def get_failure_redirect_url(tran_id, reason):
	"""Get redirect URL for failed payment"""
	site_url = frappe.utils.get_url()
	import urllib.parse
	encoded_reason = urllib.parse.quote(reason)
	return f"{site_url}/pixone/payment/failed?transaction={tran_id}&reason={encoded_reason}"
