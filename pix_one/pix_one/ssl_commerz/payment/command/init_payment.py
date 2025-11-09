"""
Init Payment Command and Handler
Location: pix_one/pix_one/ssl_commerz/payment/commands/init_payment.py
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_url
import uuid
import requests
import json


class InitPaymentCommand:
    """
    Init Payment Command
    NestJS equivalent of InitPaymentCommand
    """
    
    def __init__(self, init_payment_dto, user_id):
        """
        Initialize command with payment data and user ID
        
        Args:
            init_payment_dto (dict): Payment initialization data
            user_id (str): Current user email/ID
        """
        self.init_payment_dto = init_payment_dto
        self.user_id = user_id
    
    def execute(self):
        """
        Execute the command - delegates to handler
        """
        handler = InitPaymentHandler(self.init_payment_dto, self.user_id)
        return handler.execute()


class InitPaymentHandler:
    """
    Init Payment Handler
    NestJS equivalent of InitPaymentHandler with @CommandHandler decorator
    """
    
    def __init__(self, init_payment_dto, user_id):
        self.init_payment_dto = init_payment_dto
        self.user_id = user_id
        
        # SSLCommerz credentials (should be moved to Site Config)
        self.store_id = frappe.conf.get('sslcommerz_store_id') or 'pixfa68ac666b8316e'
        self.store_passwd = frappe.conf.get('sslcommerz_store_passwd') or 'pixfa68ac666b8316e@ssl'
        self.is_live = frappe.conf.get('sslcommerz_is_live') or False
        
        # API URL
        self.api_url = 'https://securepay.sslcommerz.com/gwprocess/v4/api.php' if self.is_live else 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php'
    
    def execute(self):
        """
        Execute payment initialization
        
        Returns:
            dict: SSLCommerz gateway URL and session key
        """
        try:
            # Generate unique transaction ID
            tran_id = self.init_payment_dto.get('tran_id') or str(uuid.uuid4())
            
            frappe.logger().info(f"Initializing payment with tran_id: {tran_id}")
            
            # Get site URL for callbacks
            site_url = get_url()
            
            # Prepare payment data
            data = {
                'store_id': self.store_id,
                'store_passwd': self.store_passwd,
                'total_amount': self.init_payment_dto.get('amount', 100),
                'currency': self.init_payment_dto.get('currency', 'BDT'),
                'tran_id': tran_id,
                'success_url': self.init_payment_dto.get('success_url') or f'{site_url}/api/method/pix_one.ssl_commerz.api.payment_api.payment_success',
                'fail_url': self.init_payment_dto.get('fail_url') or f'{site_url}/api/method/pix_one.ssl_commerz.api.payment_api.payment_fail',
                'cancel_url': self.init_payment_dto.get('cancel_url') or f'{site_url}/api/method/pix_one.ssl_commerz.api.payment_api.payment_cancel',
                'ipn_url': self.init_payment_dto.get('ipn_url') or f'{site_url}/api/method/pix_one.ssl_commerz.api.payment_api.payment_ipn',
                'shipping_method': 'Courier',
                'product_name': self.init_payment_dto.get('product_name', 'Product'),
                'product_category': self.init_payment_dto.get('product_category', 'General'),
                'product_profile': 'general',
                'cus_name': self.init_payment_dto.get('cus_name', 'Customer Name'),
                'cus_email': self.init_payment_dto.get('cus_email', 'customer@example.com'),
                'cus_add1': self.init_payment_dto.get('cus_add1', 'Dhaka'),
                'cus_add2': self.init_payment_dto.get('cus_add2', 'Dhaka'),
                'cus_city': self.init_payment_dto.get('cus_city', 'Dhaka'),
                'cus_state': self.init_payment_dto.get('cus_state', 'Dhaka'),
                'cus_postcode': self.init_payment_dto.get('cus_postcode', '1000'),
                'cus_country': self.init_payment_dto.get('cus_country', 'Bangladesh'),
                'cus_phone': self.init_payment_dto.get('cus_phone', '01711111111'),
                'cus_fax': self.init_payment_dto.get('cus_fax', '01711111111'),
                'ship_name': self.init_payment_dto.get('ship_name', 'Customer Name'),
                'ship_add1': self.init_payment_dto.get('ship_add1', 'Dhaka'),
                'ship_add2': self.init_payment_dto.get('ship_add2', 'Dhaka'),
                'ship_city': self.init_payment_dto.get('ship_city', 'Dhaka'),
                'ship_state': self.init_payment_dto.get('ship_state', 'Dhaka'),
                'ship_postcode': self.init_payment_dto.get('ship_postcode', '1000'),
                'ship_country': self.init_payment_dto.get('ship_country', 'Bangladesh'),
            }
            
            # Call SSLCommerz API
            response = self._call_sslcommerz_api(data)
            
            # Create payment record in database
            payment_doc = self._create_payment_record(tran_id, data, response)
            
            frappe.logger().info(f"Payment record created: {payment_doc.name}")
            
            return response
            
        except Exception as e:
            frappe.logger().error(f"Error initializing payment: {str(e)}")
            frappe.log_error(f"Init Payment Error: {str(e)}", "SSL Payment Init")
            frappe.throw(_("Payment initialization failed: {0}").format(str(e)))
    
    def _call_sslcommerz_api(self, data):
        """
        Call SSLCommerz API to initialize payment
        
        Args:
            data (dict): Payment data
            
        Returns:
            dict: SSLCommerz response
        """
        try:
            # Make POST request to SSLCommerz
            response = requests.post(
                self.api_url,
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            # Check if request was successful
            if result.get('status') != 'SUCCESS':
                error_message = result.get('failedreason', 'Unknown error')
                raise Exception(f"SSLCommerz API Error: {error_message}")
            
            return result
            
        except requests.RequestException as e:
            frappe.logger().error(f"SSLCommerz API Request Error: {str(e)}")
            raise Exception(f"Failed to connect to SSLCommerz: {str(e)}")
    
    def _create_payment_record(self, tran_id, payment_data, sslcommerz_response):
        """
        Create payment record in SSL Payment doctype
        
        Args:
            tran_id (str): Transaction ID
            payment_data (dict): Payment initialization data
            sslcommerz_response (dict): Response from SSLCommerz
            
        Returns:
            frappe.Document: Created payment document
        """
        try:
            # Create SSL Payment document
            payment_doc = frappe.get_doc({
                'doctype': 'SSL Payment',
                'transaction_id': tran_id,
                'amount': payment_data['total_amount'],
                'currency': payment_data['currency'],
                'status': 'Pending',
                'customer_name': payment_data['cus_name'],
                'customer_email': payment_data['cus_email'],
                'customer_phone': payment_data['cus_phone'],
                'tran_date': now_datetime(),
                'api_response': json.dumps(sslcommerz_response),
                # Store user reference if needed
                'owner': self.user_id
            })
            
            # Insert document
            payment_doc.insert(ignore_permissions=True)
            
            # Commit to database
            frappe.db.commit()
            
            return payment_doc
            
        except Exception as e:
            frappe.logger().error(f"Error creating payment record: {str(e)}")
            frappe.db.rollback()
            raise Exception(f"Failed to create payment record: {str(e)}")


# ============================================
# Alternative: Simple function-based approach
# ============================================

def init_payment_simple(init_payment_dto, user_id):
    """
    Simplified version without CQRS pattern
    Can be used directly from payment_api.py
    """
    command = InitPaymentCommand(init_payment_dto, user_id)
    return command.execute()