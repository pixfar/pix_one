import frappe
from frappe import _
from pix_one.common.shared import BaseDataService
from sslcommerz_lib import SSLCOMMERZ
import json
import uuid
from frappe import utils


@frappe.whitelist(allow_guest=True)
def initiate_payment(planId = None):
    """
    Initiate SSLCommerz payment session
    """
    try:

        user = BaseDataService.get_current_user()
        if planId is None:
            frappe.throw(_("Plan ID is required to initiate payment."))

        planDetails = BaseDataService.get_single_doc(
            doctype="SaaS Subscription Plan",
            name=planId,
            fields="*"
        )
        if not planDetails:
            frappe.throw(_("Invalid Plan ID provided."))
        
        

        settings = get_sslcommerz_settings()
        sslcz = SSLCOMMERZ(settings)
        site_url = frappe.utils.get_url()
        tran_id = generate_transaction_id()

        # Extract contact information from user data
        contact = user[0].get('contacts', [{}])[0] if user and len(user) > 0 and user[0].get('contacts') else {}
        user_info = user[0] if user and len(user) > 0 else {}

        # Get customer details with fallbacks
        customer_name = contact.get('full_name') or user_info.get('full_name') or user_info.get('first_name', 'Guest')
        customer_email = contact.get('email_id') or user_info.get('email', '')
        customer_phone = contact.get('mobile_no') or contact.get('phone') or '01700000000'

        # Parse address if available (format: "address-type")
        customer_address = contact.get('address', 'Dhaka')
        if '-' in customer_address:
            customer_address = customer_address.split('-')[0].strip()

        # Extract city from address or use default
        customer_city = 'Dhaka'
        customer_country = 'Bangladesh'

        # Build product information
        product_name = f"{planDetails.get('plan_name')} - {planDetails.get('billing_interval', 'Monthly')}"
        product_category = 'SaaS Subscription'

        # Build post body for SSLCommerz
        post_body = {
            'total_amount': float(planDetails.get('price')),
            'currency': planDetails.get('currency', 'BDT'),
            'tran_id': tran_id,
            'success_url': f"{site_url}/api/method/pix_one.api.payments.payment_success.payment_success_service.payment_success",
            'fail_url': f"{site_url}/api/method/pix_one.api.payments.payment_fail.payment_fail_service.payment_fail",
            'cancel_url': f"{site_url}/api/method/pix_one.api.payments.payment_cancel.payment_cancel_service.payment_cancel",
            'emi_option': 0,
            'cus_name': customer_name,
            'cus_email': customer_email,
            'cus_phone': customer_phone,
            'cus_add1': customer_address,
            'cus_city': customer_city,
            'cus_country': customer_country,
            'shipping_method': 'NO',
            'num_of_item': 1,
            'product_name': product_name,
            'product_category': product_category,
            'product_profile': 'general',
            # Pass subscription reference through value fields
            'value_a': planDetails.get('name', ''),  # Plan ID/Name
            'value_b': planDetails.get('plan_code', ''),  # Plan Code
            'value_c': customer_email,  # Customer Email/ID
            'value_d': 'Initial Payment'  # Transaction Type
        }
        # Create SSLCommerz session
        response = sslcz.createSession(post_body)
        if not response:
            frappe.throw(_("Failed to connect to Payment gateway."))

        create_saas_payment_transaction(tran_id, planId, customer_email, post_body, response)
        create_payment_log(tran_id, customer_email, post_body, response)
            

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
    sslcommerz_settings = frappe.get_doc('PixOne System Settings')
    store_id = sslcommerz_settings.ssl_store_id
    store_pass = sslcommerz_settings.ssl_store_password
    is_sandbox = sslcommerz_settings.is_sandbox
    
    return {
        'store_id': store_id,
        'store_pass': store_pass,
        'issandbox': is_sandbox
    }


def generate_transaction_id():
    """Generate unique transaction ID"""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


def create_saas_payment_transaction(tran_id, subscription_id, user_id, request_data, response_data):
    """Create a SaaS Payment Transaction for subscription payments"""
    try:
        
        payment_transaction = frappe.get_doc({
            'doctype': 'SaaS Payment Transaction',
            'transaction_id': tran_id,
            'subscription_id': subscription_id,
            'customer_id': user_id,
            'amount': float(request_data.get('total_amount')),
            'currency': request_data.get('currency', 'BDT'),
            'payment_date': utils.now(),
            'payment_gateway': 'SSLCommerz',
            'status': 'Initiated',
            'transaction_type': request_data.get('value_d', 'Initial Payment'),
            'gateway_response': json.dumps(response_data, indent=2),
            'gateway_status': response_data.get('status'),
            'is_recurring': False
        })
        payment_transaction.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create SaaS payment transaction: {str(e)}", "SaaS Payment Transaction Creation")


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