"""
Payment Success Command and Handler
Location: pix_one/pix_one/ssl_commerz/payment/commands/success_payment.py
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
import json


class PaymentSuccessCommand:
    """
    Payment Success Command
    NestJS equivalent of PaymentSuccessStatusCommand
    """
    
    def __init__(self, payment_info):
        """
        Initialize command with payment info from SSLCommerz
        
        Args:
            payment_info (dict): Payment information from SSLCommerz callback
        """
        self.payment_info = payment_info
    
    def execute(self):
        """
        Execute the command - delegates to handler
        """
        handler = PaymentSuccessHandler(self.payment_info)
        return handler.execute()


class PaymentSuccessHandler:
    """
    Payment Success Handler
    NestJS equivalent of PaymentSuccessStatusHandler with @CommandHandler decorator
    """
    
    def __init__(self, payment_info):
        self.payment_info = payment_info
    
    def execute(self):
        """
        Handle payment success callback from SSLCommerz
        
        Returns:
            dict: Success response with redirect URL
        """
        try:
            tran_id = self.payment_info.get('tran_id')
            
            if not tran_id:
                frappe.throw(_("Transaction ID not found in payment info"))
            
            frappe.logger().info(f"Processing payment success for tran_id: {tran_id}")
            frappe.logger().info(f"Payment Info: {json.dumps(self.payment_info)}")
            
            # Find payment record
            payment_doc = self._get_payment_by_transaction_id(tran_id)
            
            if not payment_doc:
                frappe.throw(_("Payment not found"))
            
            # Update payment status with transaction
            updated_payment = self._update_payment_status(payment_doc, self.payment_info)
            
            frappe.logger().info(f"Payment status updated successfully: {tran_id}")
            
            # Publish event (Frappe equivalent of EventBus)
            self._publish_payment_success_event(updated_payment)
            
            # Get redirect URL from site config or use default
            redirect_url = frappe.conf.get('payment_success_redirect_url') or 'http://localhost:5173/profile'
            
            return {
                'message': 'Payment status updated successfully',
                'payment': self._serialize_payment(updated_payment),
                'redirect_to': redirect_url
            }
            
        except Exception as e:
            frappe.logger().error(f"Error processing payment success: {str(e)}")
            frappe.log_error(f"Payment Success Error: {str(e)}", "SSL Payment Success")
            
            # Rollback if transaction failed
            frappe.db.rollback()
            
            frappe.throw(_("Failed to process payment success: {0}").format(str(e)))
    
    def _get_payment_by_transaction_id(self, tran_id):
        """
        Get payment document by transaction ID
        
        Args:
            tran_id (str): Transaction ID
            
        Returns:
            frappe.Document: Payment document or None
        """
        try:
            # Find payment by transaction_id
            payment_name = frappe.db.get_value(
                'SSL Payment',
                {'transaction_id': tran_id},
                'name'
            )
            
            if not payment_name:
                return None
            
            return frappe.get_doc('SSL Payment', payment_name)
            
        except Exception as e:
            frappe.logger().error(f"Error finding payment: {str(e)}")
            return None
    
    def _update_payment_status(self, payment_doc, payment_info):
        """
        Update payment status in database (with transaction)
        Frappe equivalent of Prisma.$transaction
        
        Args:
            payment_doc (frappe.Document): Payment document
            payment_info (dict): Payment info from SSLCommerz
            
        Returns:
            frappe.Document: Updated payment document
        """
        try:
            # Start transaction (Frappe auto-manages transactions)
            # Update payment document
            payment_doc.status = 'Success'
            payment_doc.card_type = payment_info.get('card_brand') or payment_info.get('card_type')
            payment_doc.bank_tran_id = payment_info.get('bank_tran_id')
            payment_doc.val_id = payment_info.get('val_id')
            payment_doc.currency = payment_info.get('currency_type', 'BDT')
            payment_doc.store_amount = payment_info.get('store_amount')
            payment_doc.risk_level = payment_info.get('risk_level')
            
            # Update transaction date if provided
            if payment_info.get('tran_date'):
                payment_doc.tran_date = payment_info.get('tran_date')
            
            # Store full API response
            payment_doc.api_response = json.dumps(payment_info)
            
            # Save document
            payment_doc.save(ignore_permissions=True)
            
            # If submittable, submit the document
            if payment_doc.meta.is_submittable and payment_doc.docstatus == 0:
                payment_doc.submit()
            
            # Commit transaction
            frappe.db.commit()
            
            return payment_doc
            
        except Exception as e:
            frappe.logger().error(f"Error updating payment: {str(e)}")
            frappe.db.rollback()
            raise
    
    def _publish_payment_success_event(self, payment_doc):
        """
        Publish payment success event
        Frappe equivalent of EventBus.publish()
        
        Args:
            payment_doc (frappe.Document): Payment document
        """
        try:
            # Trigger Frappe document event
            payment_doc.run_method('on_payment_success')
            
            # Trigger custom event (if event handler exists)
            frappe.publish_realtime(
                event='payment_success',
                message={
                    'transaction_id': payment_doc.transaction_id,
                    'amount': payment_doc.amount,
                    'status': payment_doc.status,
                    'customer_email': payment_doc.customer_email
                },
                user=payment_doc.owner
            )
            
            # Call event handler if exists
            from pix_one.pix_one.ssl_commerz.events.payment_events import handle_payment_success
            handle_payment_success(payment_doc)
            
        except ImportError:
            # Event handler not implemented yet
            frappe.logger().info("Payment success event handler not found, skipping event")
            pass
        except Exception as e:
            # Don't fail the main flow if event publishing fails
            frappe.logger().error(f"Error publishing payment success event: {str(e)}")
    
    def _serialize_payment(self, payment_doc):
        """
        Serialize payment document for API response
        
        Args:
            payment_doc (frappe.Document): Payment document
            
        Returns:
            dict: Serialized payment data
        """
        return {
            'name': payment_doc.name,
            'transaction_id': payment_doc.transaction_id,
            'amount': payment_doc.amount,
            'currency': payment_doc.currency,
            'status': payment_doc.status,
            'customer_name': payment_doc.customer_name,
            'customer_email': payment_doc.customer_email,
            'customer_phone': payment_doc.customer_phone,
            'card_type': payment_doc.card_type,
            'bank_tran_id': payment_doc.bank_tran_id,
            'tran_date': str(payment_doc.tran_date) if payment_doc.tran_date else None,
            'created_at': str(payment_doc.creation),
            'updated_at': str(payment_doc.modified)
        }


# ============================================
# Event Handler (to be created separately)
# ============================================

"""
Location: pix_one/pix_one/ssl_commerz/events/payment_events.py

def handle_payment_success(payment_doc):
    '''
    Handle payment success event
    Equivalent to PaymentSuccessEvent handler in NestJS
    '''
    # Send email notification
    # Update related documents (Sales Invoice, etc.)
    # Trigger webhooks
    # etc.
    pass
"""