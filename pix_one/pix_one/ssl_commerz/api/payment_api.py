"""
SSL Payment Controller - Frappe API Endpoints
Location: pix_one/pix_one/ssl_commerz/api/payment_api.py

এটি NestJS Controller এর Python equivalent
"""

import frappe
from frappe import _
from frappe.utils import cint
import json

# Import commands
from pix_one.ssl_commerz.payment.commands.init_payment import InitPaymentCommand
from pix_one.ssl_commerz.payment.commands.success_payment import PaymentSuccessCommand
from pix_one.ssl_commerz.payment.commands.fail_payment import PaymentFailCommand
from pix_one.ssl_commerz.payment.commands.cancel_payment import PaymentCancelCommand
from pix_one.ssl_commerz.payment.commands.ipn_payment import PaymentIpnCommand

# Import queries
from pix_one.ssl_commerz.payment.queries.get_payments import GetMyPaymentsQuery


@frappe.whitelist()
def init_payment(init_payment_dto):
    """
    Initialize payment
    POST /api/method/pix_one.ssl_commerz.api.payment_api.init_payment
    
    Requires authentication
    """
    try:
        # Get current user
        user_id = frappe.session.user
        
        # Parse DTO if it's a string
        if isinstance(init_payment_dto, str):
            init_payment_dto = json.loads(init_payment_dto)
        
        # Execute command
        command = InitPaymentCommand(init_payment_dto, user_id)
        result = command.execute()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Init Payment Error: {str(e)}", "SSL Payment")
        frappe.throw(_("Failed to initialize payment: {0}").format(str(e)))


@frappe.whitelist(allow_guest=True)
def payment_success():
    """
    Payment success callback from SSLCommerz
    POST /api/method/pix_one.ssl_commerz.api.payment_api.payment_success
    
    No authentication required (callback from SSLCommerz)
    """
    try:
        # Get form data from request
        payment_info = frappe.form_dict
        
        # Execute command
        command = PaymentSuccessCommand(payment_info)
        result = command.execute()
        
        if result and result.get('redirect_to'):
            # Redirect user to success page
            frappe.local.response['type'] = 'redirect'
            frappe.local.response['location'] = result['redirect_to']
        else:
            frappe.throw(_("Payment not found"), frappe.DoesNotExistError)
            
    except Exception as e:
        frappe.log_error(f"Payment Success Error: {str(e)}", "SSL Payment")
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['message'] = str(e)


@frappe.whitelist(allow_guest=True)
def payment_fail():
    """
    Payment fail callback from SSLCommerz
    POST /api/method/pix_one.ssl_commerz.api.payment_api.payment_fail
    
    No authentication required (callback from SSLCommerz)
    """
    try:
        # Get form data from request
        payment_info = frappe.form_dict
        
        # Execute command
        command = PaymentFailCommand(payment_info)
        result = command.execute()
        
        if result and result.get('redirect_to'):
            # Redirect user to fail page
            frappe.local.response['type'] = 'redirect'
            frappe.local.response['location'] = result['redirect_to']
        else:
            frappe.throw(_("Payment not found"), frappe.DoesNotExistError)
            
    except Exception as e:
        frappe.log_error(f"Payment Fail Error: {str(e)}", "SSL Payment")
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['message'] = str(e)


@frappe.whitelist(allow_guest=True)
def payment_cancel():
    """
    Payment cancel callback from SSLCommerz
    POST /api/method/pix_one.ssl_commerz.api.payment_api.payment_cancel
    
    No authentication required (callback from SSLCommerz)
    """
    try:
        # Get form data from request
        payment_info = frappe.form_dict
        
        # Execute command
        command = PaymentCancelCommand(payment_info)
        result = command.execute()
        
        if result and result.get('redirect_to'):
            # Redirect user to cancel page
            frappe.local.response['type'] = 'redirect'
            frappe.local.response['location'] = result['redirect_to']
        else:
            frappe.throw(_("Payment not found"), frappe.DoesNotExistError)
            
    except Exception as e:
        frappe.log_error(f"Payment Cancel Error: {str(e)}", "SSL Payment")
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['message'] = str(e)


@frappe.whitelist(allow_guest=True)
def payment_ipn():
    """
    Payment IPN (Instant Payment Notification) callback from SSLCommerz
    POST /api/method/pix_one.ssl_commerz.api.payment_api.payment_ipn
    
    No authentication required (callback from SSLCommerz)
    """
    try:
        # Get form data from request
        payment_info = frappe.form_dict
        
        # Execute command
        command = PaymentIpnCommand(payment_info)
        result = command.execute()
        
        # IPN doesn't redirect, just returns status
        return {
            "status": "success" if result else "failed",
            "message": "IPN processed successfully" if result else "IPN processing failed"
        }
            
    except Exception as e:
        frappe.log_error(f"Payment IPN Error: {str(e)}", "SSL Payment")
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist()
def get_my_payments(page=1, page_size=20, sort_by="creation", sort_order="desc"):
    """
    Get logged-in user's payments
    GET /api/method/pix_one.ssl_commerz.api.payment_api.get_my_payments
    
    Requires authentication
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20)
    - sort_by: Sort field (default: creation)
    - sort_order: asc or desc (default: desc)
    """
    try:
        # Get current user
        user_id = frappe.session.user
        
        # Create pagination params
        pagination = {
            "page": cint(page),
            "page_size": cint(page_size),
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        # Execute query
        query = GetMyPaymentsQuery(pagination, user_id)
        result = query.execute()
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Get My Payments Error: {str(e)}", "SSL Payment")
        frappe.throw(_("Failed to get payments: {0}").format(str(e)))


# ============================================
# Helper function for error handling
# ============================================

def handle_payment_callback_error(error, callback_type):
    """
    Common error handler for payment callbacks
    """
    frappe.log_error(
        f"{callback_type} Error: {str(error)}", 
        f"SSL Payment {callback_type}"
    )
    
    # Return error page or JSON
    if frappe.local.request.headers.get('Accept') == 'application/json':
        frappe.local.response['http_status_code'] = 500
        return {
            "status": "error",
            "message": str(error)
        }
    else:
        # Redirect to error page
        frappe.local.response['type'] = 'redirect'
        frappe.local.response['location'] = '/payment-error'