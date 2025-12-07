import frappe
from frappe import _
from pix_one.api.payments.init_payment.init_payment_service import initiate_payment, get_sslcommerz_settings, generate_transaction_id, create_payment_log
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions
from sslcommerz_lib import SSLCOMMERZ
import json


@frappe.whitelist()
@handle_exceptions
def init_subscription_payment(subscription_id):
    """
    Initialize payment for a subscription using only subscription ID.
    Fetches customer info from session user and subscription details from database.

    Args:
        subscription_id: SaaS Subscriptions document name

    Returns:
        {
            "status": "success",
            "gateway_url": "https://...",
            "transaction_id": "...",
            "session_key": "...",
            "subscription_id": "..."
        }
    """
    # Get current logged-in user
    current_user = frappe.session.user

    if current_user == 'Guest':
        frappe.throw(_("Please login to continue with payment"))

    # Get subscription details
    subscription = frappe.get_doc('SaaS Subscriptions', subscription_id)

    # Verify subscription belongs to current user
    if subscription.customer_id != current_user:
        frappe.throw(_("Unauthorized access to subscription"))

    # Verify subscription status allows payment
    if subscription.status not in ['Pending Payment', 'Past Due', 'Expired']:
        frappe.throw(_("This subscription does not require payment"))

    # Get plan details
    plan = frappe.get_doc('SaaS Subscription Plan', subscription.plan_name)

    # Get customer/user details
    user_doc = frappe.get_doc('User', current_user)

    # Get additional customer info if available
    customer_name = user_doc.full_name or user_doc.first_name or current_user
    customer_email = user_doc.email
    customer_phone = user_doc.phone or user_doc.mobile_no or '01700000000'  # Default if not set

    # Prepare address (you can enhance this to get from Customer or Address doctype)
    customer_address = 'Dhaka'  # Default
    customer_city = 'Dhaka'  # Default
    customer_country = 'Bangladesh'  # Default

    # Get SSLCommerz settings
    settings = get_sslcommerz_settings()

    # Initialize SSLCommerz
    sslcz = SSLCOMMERZ(settings)

    # Generate unique transaction ID
    tran_id = generate_transaction_id()

    # Get site URL for callback URLs
    site_url = frappe.utils.get_url()

    # Calculate total amount (subscription price + setup fee if applicable)
    total_amount = float(subscription.price)
    if plan.setup_fee and subscription.status == 'Pending Payment':
        total_amount += float(plan.setup_fee)

    # Determine transaction type
    if subscription.status == 'Pending Payment':
        transaction_type = 'Initial Payment'
    elif subscription.status == 'Past Due':
        transaction_type = 'Recurring Payment'
    elif subscription.status == 'Expired':
        transaction_type = 'Renewal'
    else:
        transaction_type = 'Payment'

    # Build post body for SSLCommerz
    post_body = {
        'total_amount': total_amount,
        'currency': subscription.currency or 'BDT',
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
        'product_name': f"{plan.plan_name} - {subscription.billing_interval}",
        'product_category': 'Subscription',
        'product_profile': 'general',
        # Custom fields to pass subscription context
        'value_a': subscription_id,  # Subscription ID
        'value_b': plan.plan_name,  # Plan name
        'value_c': current_user,  # Customer ID
        'value_d': transaction_type,  # Transaction type
    }

    # Create SSLCommerz session
    response = sslcz.createSession(post_body)

    # Log the transaction
    create_payment_log(tran_id, current_user, post_body, response)

    # Check if session creation was successful
    if response.get('status') == 'SUCCESS':
        # Create SaaS Payment Transaction record
        payment_transaction = frappe.get_doc({
            'doctype': 'SaaS Payment Transaction',
            'transaction_id': tran_id,
            'subscription_id': subscription_id,
            'customer_id': current_user,
            'amount': total_amount,
            'currency': subscription.currency or 'BDT',
            'payment_gateway': 'SSLCommerz',
            'status': 'Initiated',
            'transaction_type': transaction_type,
            'gateway_transaction_id': response.get('sessionkey'),
            'gateway_response': json.dumps(response, indent=2)
        })
        payment_transaction.insert(ignore_permissions=True)
        frappe.db.commit()

        return ResponseFormatter.success(
            data={
                'gateway_url': response.get('GatewayPageURL'),
                'transaction_id': tran_id,
                'session_key': response.get('sessionkey'),
                'subscription_id': subscription_id
            },
            message='Payment session created successfully'
        )
    else:
        frappe.log_error(f"SSLCommerz Error: {response}", "SSLCommerz Subscription Payment Init")
        frappe.throw(_("Failed to create payment session: {0}").format(
            response.get('failedreason', 'Unknown error')
        ))
