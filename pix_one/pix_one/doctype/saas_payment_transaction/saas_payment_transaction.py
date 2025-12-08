# Copyright (c) 2025, Pix One and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SaaSPaymentTransaction(Document):
	def before_save(self):
		"""Set defaults before save"""
		# Set transaction_id from name if not set
		if not self.transaction_id:
			self.transaction_id = self.name

	@frappe.whitelist()
	def mark_as_completed(self, gateway_transaction_id=None, gateway_response=None):
		"""Mark payment as completed and process"""
		from pix_one.utils.payment_processor import PaymentProcessor
		return PaymentProcessor.process_payment_success(
			self.name,
			gateway_transaction_id,
			gateway_response
		)

	@frappe.whitelist()
	def mark_as_failed(self, failure_reason=None, gateway_response=None):
		"""Mark payment as failed"""
		from pix_one.utils.payment_processor import PaymentProcessor
		return PaymentProcessor.process_payment_failure(
			self.name,
			failure_reason,
			gateway_response
		)
