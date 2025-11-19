import frappe
from frappe import _
from sslcommerz_lib import SSLCOMMERZ
import json
import uuid

@frappe.whitelist(allow_guest=True)
def initiate_payment():
    """
    Initiate SSLCommerz payment session

    Request Body (JSON):
    {
        "total_amount": 100.50,
        "currency": "BDT",
        "product_name": "Subscription Plan",
        "product_category": "Subscription",
        "cus_name": "John Doe",
        "cus_email": "john@example.com",
        "cus_phone": "01700000000",
        "cus_add1": "123 Main Street",
        "cus_city": "Dhaka",
        "cus_country": "Bangladesh",
        "num_of_item": 1,
        "shipping_method": "NO"
    }

    Returns:
    {
        "status": "success",
        "gateway_url": "https://...",
        "transaction_id": "...",
        "session_key": "..."
    }
    """
    try:
        # Get payment data from request
        payment_data = frappe.local.form_dict

        # Parse payment data if string
        if isinstance(payment_data, str):
            payment_data = json.loads(payment_data)

        # Get current user
        user_id = frappe.session.user

        # Validate required fields
        required_fields = [
            'total_amount', 'currency', 'product_name', 'product_category',
            'cus_name', 'cus_email', 'cus_phone', 'cus_add1', 'cus_city', 'cus_country'
        ]

        missing_fields = [field for field in required_fields if not payment_data.get(field)]
        if missing_fields:
            frappe.throw(_("Missing required fields: {0}").format(", ".join(missing_fields)))

        # Get SSLCommerz settings from Frappe Site Config or create default
        settings = get_sslcommerz_settings()

        # Initialize SSLCommerz
        sslcz = SSLCOMMERZ(settings)

        # Generate unique transaction ID
        tran_id = generate_transaction_id()

        # Get site URL for callback URLs
        site_url = frappe.utils.get_url()

        # Build post body for SSLCommerz
        post_body = {
            'total_amount': float(payment_data.get('total_amount')),
            'currency': payment_data.get('currency', 'BDT'),
            'tran_id': tran_id,
            'success_url': f"{site_url}/api/method/pix_one.api.payments.payment_success.payment_success_service.payment_success",
            'fail_url': f"{site_url}/api/method/pix_one.api.payments.payment_fail.payment_fail_service.payment_fail",
            'cancel_url': f"{site_url}/api/method/pix_one.api.payments.payment_cancel.payment_cancel_service.payment_cancel",
            'emi_option': 0,
            'cus_name': payment_data.get('cus_name'),
            'cus_email': payment_data.get('cus_email'),
            'cus_phone': payment_data.get('cus_phone'),
            'cus_add1': payment_data.get('cus_add1'),
            'cus_city': payment_data.get('cus_city'),
            'cus_country': payment_data.get('cus_country'),
            'shipping_method': payment_data.get('shipping_method', 'NO'),
            'multi_card_name': payment_data.get('multi_card_name', ''),
            'num_of_item': payment_data.get('num_of_item', 1),
            'product_name': payment_data.get('product_name'),
            'product_category': payment_data.get('product_category'),
            'product_profile': payment_data.get('product_profile', 'general')
        }

        # Add optional fields if provided
        if payment_data.get('cus_add2'):
            post_body['cus_add2'] = payment_data.get('cus_add2')
        if payment_data.get('cus_state'):
            post_body['cus_state'] = payment_data.get('cus_state')
        if payment_data.get('cus_postcode'):
            post_body['cus_postcode'] = payment_data.get('cus_postcode')

        # Create SSLCommerz session
        response = sslcz.createSession(post_body)

        # Log the transaction in Frappe
        create_payment_log(tran_id, user_id, post_body, response)

        # Check if session creation was successful
        if response.get('status') == 'SUCCESS':
            return {
                'status': 'success',
                'gateway_url': response.get('GatewayPageURL'),
                'transaction_id': tran_id,
                'session_key': response.get('sessionkey'),
                'message': 'Payment session created successfully'
            }
        else:
            frappe.log_error(f"SSLCommerz Error: {response}", "SSLCommerz Payment Init")
            return {
                'status': 'failed',
                'message': response.get('failedreason', 'Failed to create payment session'),
                'error': response
            }

    except Exception as e:
        frappe.log_error(f"Payment Init Error: {str(e)}\n{frappe.get_traceback()}", "Payment Init API")
        frappe.throw(_("Failed to initiate payment: {0}").format(str(e)))


def get_sslcommerz_settings():
    """Get SSLCommerz configuration from site config or database"""
    # Try to get from site config first
    store_id = frappe.conf.get('sslcommerz_store_id')
    store_pass = frappe.conf.get('sslcommerz_store_pass')
    is_sandbox = frappe.conf.get('sslcommerz_sandbox', True)

    # If not in config, use default test credentials
    if not store_id or not store_pass:
        store_id = 'testbox'
        store_pass = 'qwerty'
        is_sandbox = True

    return {
        'store_id': store_id,
        'store_pass': store_pass,
        'issandbox': is_sandbox
    }


def generate_transaction_id():
    """Generate unique transaction ID"""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


def create_payment_log(tran_id, user_id, request_data, response_data):
    """Create a payment log entry in SSL Payment doctype"""
    try:
        payment_log = frappe.get_doc({
            'doctype': 'SSL Payment',
            'transaction_id': tran_id,
            'user': user_id,
            'amount': request_data.get('total_amount'),
            'currency': request_data.get('currency'),
            'status': 'Initiated',
            'customer_name': request_data.get('cus_name'),
            'customer_email': request_data.get('cus_email'),
            'customer_phone': request_data.get('cus_phone'),
            'product_name': request_data.get('product_name'),
            'request_data': json.dumps(request_data, indent=2),
            'response_data': json.dumps(response_data, indent=2)
        })
        payment_log.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create payment log: {str(e)}", "Payment Log Creation")