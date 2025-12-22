# Copyright (c) 2025, PixOne and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, now_datetime


class SaaSCompany(Document):
	def before_insert(self):
		"""Set defaults before inserting"""
		if not self.created_by_user:
			self.created_by_user = frappe.session.user

		if not self.customer_id:
			self.customer_id = frappe.session.user

		# Generate site name from company name if not provided
		# if not self.site_name:
		# 	self.site_name = self._generate_site_name()

		# Set site URL
		if not self.site_url:
			self.site_url = self._generate_site_url()

	def validate(self):
		"""Validate the document"""
		self.validate_subscription_quota()
		self.validate_site_name()

		# Set subscription_id from customer if not set
		if not self.subscription_id and self.customer_id:
			self.auto_set_subscription()

	def after_insert(self):
		"""After insert hook"""
		# Update subscription company count
		self.update_subscription_company_count()

	def on_trash(self):
		"""Before delete hook"""
		# Update subscription company count
		self.update_subscription_company_count(decrement=True)

	def _generate_site_name(self):
		"""Generate a unique site name from company name"""
		import re

		# Sanitize company name: lowercase, replace spaces with hyphens, remove special chars
		base_name = re.sub(r'[^a-z0-9-]', '', self.company_name.lower().replace(' ', '-'))
		base_name = re.sub(r'-+', '-', base_name).strip('-')  # Remove multiple hyphens

		# Limit length
		base_name = base_name[:50]

		# Check uniqueness
		site_name = base_name
		counter = 1
		while frappe.db.exists("SaaS Company", {"site_name": site_name}):
			site_name = f"{base_name}-{counter}"
			counter += 1

		return site_name

	def _generate_site_url(self):
		"""Generate site URL"""
		# Use custom domain if provided, otherwise use localhost pattern
		if self.domain:
			# Use the custom domain provided by user
			protocol = "https" if "." in self.domain and not "localhost" in self.domain else "http"
			return f"{protocol}://{self.domain}"
		else:
			# Default to localhost pattern
			return f"http://{self.site_name}.localhost:8000"

	def validate_site_name(self):
		"""Validate site name format"""
		pass
		# import re
		# if self.site_name:
		# 	# Site name should be lowercase alphanumeric with hyphens
		# 	if not re.match(r'^[a-z0-9-]+$', self.site_name):
		# 		frappe.throw("Site name can only contain lowercase letters, numbers, and hyphens")

		# 	if len(self.site_name) < 3:
		# 		frappe.throw("Site name must be at least 3 characters long")

		# 	if len(self.site_name) > 63:
		# 		frappe.throw("Site name must be less than 63 characters")

	def validate_subscription_quota(self):
		"""Check if user has reached max companies in their subscription plan"""
		if not self.subscription_id:
			return

		subscription = frappe.get_doc("SaaS Subscriptions", self.subscription_id)

		# Get plan limits
		plan = frappe.get_doc("SaaS Subscription Plan", subscription.plan_name)
		max_companies = plan.max_companies or 1

		# Count existing companies for this subscription
		existing_count = frappe.db.count("SaaS Company", {
			"subscription_id": self.subscription_id,
			"status": ["not in", ["Deleted", "Failed"]],
			"name": ["!=", self.name]  # Exclude current document if updating
		})

		if existing_count >= max_companies:
			frappe.throw(
				f"Company limit reached. Your plan allows {max_companies} "
				f"{'company' if max_companies == 1 else 'companies'}. "
				f"Please upgrade your subscription to create more companies."
			)

	def auto_set_subscription(self):
		"""Auto-set subscription from customer's active subscription"""
		subscription = frappe.db.get_value(
			"SaaS Subscriptions",
			{
				"customer_id": self.customer_id,
				"status": "Active"
			},
			"name",
			order_by="creation desc"
		)

		if subscription:
			self.subscription_id = subscription

	def update_subscription_company_count(self, decrement=False):
		"""Update the current_companies count in subscription"""
		if not self.subscription_id:
			return

		try:
			subscription = frappe.get_doc("SaaS Subscriptions", self.subscription_id)

			# Count active companies
			company_count = frappe.db.count("SaaS Company", {
				"subscription_id": self.subscription_id,
				"status": ["not in", ["Deleted", "Failed"]]
			})

			subscription.db_set("current_companies", company_count, update_modified=False)

			# Also update license validation
			self._update_license_company_count(company_count)

		except Exception as e:
			frappe.log_error(f"Error updating subscription company count: {str(e)}")

	def _update_license_company_count(self, count):
		"""Update company count in license validation"""
		if not self.subscription_id:
			return

		try:
			license_doc = frappe.get_value(
				"SaaS App Validation",
				{"subscription_id": self.subscription_id},
				"name"
			)

			if license_doc:
				frappe.db.set_value(
					"SaaS App Validation",
					license_doc,
					"current_companies",
					count,
					update_modified=False
				)
		except Exception as e:
			frappe.log_error(f"Error updating license company count: {str(e)}")
