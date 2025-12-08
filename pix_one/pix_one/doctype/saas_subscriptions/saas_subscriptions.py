# Copyright (c) 2025, Pixfar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, getdate, add_days


class SaaSSubscriptions(Document):
	def before_insert(self):
		"""Set defaults before insert"""
		if not self.created_by:
			self.created_by = frappe.session.user

		if not self.subscription_id:
			self.subscription_id = self.name

	def before_save(self):
		"""Update subscription_id from name"""
		if not self.subscription_id or self.subscription_id != self.name:
			self.subscription_id = self.name

		# Auto-update status based on dates
		self._update_status_from_dates()

	def on_submit(self):
		"""Actions when subscription is submitted"""
		# Ensure license key is generated
		if not self.license_key:
			from pix_one.utils.subscription_manager import SubscriptionManager
			self.license_key = SubscriptionManager._generate_license_key(self.name)
			self.save()

	def on_cancel(self):
		"""Actions when subscription is cancelled"""
		self.status = "Cancelled"
		self.cancellation_date = nowdate()

		# Revoke license
		if self.license_key and frappe.db.exists("SaaS App Validation", self.license_key):
			validation = frappe.get_doc("SaaS App Validation", self.license_key)
			validation.validation_status = "Revoked"
			validation.save(ignore_permissions=True)

	def _update_status_from_dates(self):
		"""Automatically update status based on dates"""
		if self.status in ["Cancelled", "Suspended"]:
			return

		today = getdate(nowdate())

		# Check if in trial period
		if self.trial_ends_on and getdate(self.trial_ends_on) >= today:
			if self.status != "Active":
				self.status = "Trial"
			return

		# Check if expired
		if self.end_date and getdate(self.end_date) < today:
			self.status = "Expired"
			return

		# Check if past due (7 days after end_date)
		if self.end_date and getdate(self.end_date) < today and getdate(add_days(self.end_date, 7)) >= today:
			self.status = "Past Due"
			return

	@frappe.whitelist()
	def initiate_payment(self, transaction_type="Recurring Payment"):
		"""Initiate a payment for this subscription"""
		from pix_one.utils.payment_processor import PaymentProcessor
		return PaymentProcessor.initiate_payment(self.name, transaction_type)

	@frappe.whitelist()
	def cancel_subscription(self, reason=None, notes=None):
		"""Cancel this subscription"""
		from pix_one.utils.subscription_manager import SubscriptionManager
		return SubscriptionManager.cancel_subscription(self.name, reason, notes)

	@frappe.whitelist()
	def renew_subscription(self):
		"""Renew this subscription"""
		from pix_one.utils.subscription_manager import SubscriptionManager
		return SubscriptionManager.renew_subscription(self.name)
