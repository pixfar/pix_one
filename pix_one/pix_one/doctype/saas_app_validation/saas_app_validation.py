# Copyright (c) 2025, Pix One and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime


class SaaSAppValidation(Document):
	def before_save(self):
		# Update validation status based on expiry date
		if self.license_expiry_date and not self.is_lifetime:
			from frappe.utils import getdate, nowdate
			if getdate(self.license_expiry_date) < getdate(nowdate()):
				self.validation_status = "Expired"

	def validate_license(self):
		"""Validate the license and update validation tracking"""
		self.last_validation_check = datetime.now()
		self.validation_attempts += 1
		self.access_count += 1
		self.last_accessed = datetime.now()

		# Check if license is valid
		if self.validation_status != "Active":
			return False

		# Check expiry date
		if not self.is_lifetime and self.license_expiry_date:
			from frappe.utils import getdate, nowdate
			if getdate(self.license_expiry_date) < getdate(nowdate()):
				self.validation_status = "Expired"
				self.save()
				return False

		self.save()
		return True

	def check_resource_limits(self):
		"""Check if current usage is within limits"""
		violations = []

		if self.max_users and self.current_users > self.max_users:
			violations.append(f"User limit exceeded: {self.current_users}/{self.max_users}")

		if self.max_storage_mb and self.current_storage_mb > self.max_storage_mb:
			violations.append(f"Storage limit exceeded: {self.current_storage_mb}/{self.max_storage_mb} MB")

		if self.max_companies and self.current_companies > self.max_companies:
			violations.append(f"Company limit exceeded: {self.current_companies}/{self.max_companies}")

		if violations:
			self.violation_count += len(violations)
			import json
			existing_violations = json.loads(self.violation_details) if self.violation_details else []
			existing_violations.extend([{
				"timestamp": str(datetime.now()),
				"violation": v
			} for v in violations])
			self.violation_details = json.dumps(existing_violations, indent=2)
			self.save()
			return False

		return True
