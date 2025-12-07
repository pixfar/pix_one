# Copyright (c) 2025, Pix One and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SaaSPaymentTransaction(Document):
	def before_save(self):
		# Set transaction_id from name if not set
		if not self.transaction_id:
			self.transaction_id = self.name
