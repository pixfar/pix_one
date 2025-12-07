"""
Scheduled tasks for subscription management

This module handles:
- Subscription expiry checks
- Subscription renewals
- Trial period expiry
- License validation updates
- Past due notifications
"""

import frappe
from frappe.utils import nowdate, getdate, add_days, date_diff
from datetime import datetime
import json


def check_expired_subscriptions():
	"""
	Check for expired subscriptions and update their status
	Runs daily
	"""
	try:
		today = getdate(nowdate())

		# Find all active/trial subscriptions that have passed their end date
		expired_subscriptions = frappe.get_all(
			'SaaS Subscriptions',
			filters={
				'status': ['in', ['Active', 'Trial']],
				'end_date': ['<', today]
			},
			fields=['name', 'customer_id', 'plan_name', 'end_date', 'auto_renew', 'license_key']
		)

		for sub in expired_subscriptions:
			try:
				subscription = frappe.get_doc('SaaS Subscriptions', sub['name'])

				if subscription.auto_renew and subscription.status == 'Active':
					# Mark as past due for auto-renewal subscriptions
					subscription.status = 'Past Due'
					subscription.save(ignore_permissions=True)

					# Send reminder email
					send_renewal_reminder(subscription)

					frappe.log_error(
						f"Subscription {subscription.name} marked as Past Due",
						"Subscription Expiry Check"
					)
				else:
					# Mark as expired
					subscription.status = 'Expired'
					subscription.save(ignore_permissions=True)

					# Update license status
					if subscription.license_key:
						update_license_status(subscription.license_key, 'Expired')

					# Send expiry notification
					send_expiry_notification(subscription)

					frappe.log_error(
						f"Subscription {subscription.name} marked as Expired",
						"Subscription Expiry Check"
					)

			except Exception as e:
				frappe.log_error(
					f"Failed to process expired subscription {sub['name']}: {str(e)}",
					"Subscription Expiry Error"
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			f"Subscription expiry check failed: {str(e)}\n{frappe.get_traceback()}",
			"Subscription Expiry Check Error"
		)


def check_trial_expiry():
	"""
	Check for trial subscriptions that have expired
	Runs daily
	"""
	try:
		today = getdate(nowdate())

		# Find trial subscriptions that have passed their trial end date
		trial_expired = frappe.get_all(
			'SaaS Subscriptions',
			filters={
				'status': 'Trial',
				'trial_ends_on': ['<', today]
			},
			fields=['name', 'customer_id', 'plan_name', 'trial_ends_on']
		)

		for sub in trial_expired:
			try:
				subscription = frappe.get_doc('SaaS Subscriptions', sub['name'])

				# Check if payment was made
				completed_payment = frappe.db.exists(
					'SAAS Payment Transaction',
					{
						'subscription_id': subscription.name,
						'status': 'Completed'
					}
				)

				if completed_payment:
					# Activate subscription
					subscription.status = 'Active'
				else:
					# Mark as expired
					subscription.status = 'Expired'

				subscription.save(ignore_permissions=True)

				# Send notification
				send_trial_expiry_notification(subscription)

			except Exception as e:
				frappe.log_error(
					f"Failed to process trial expiry {sub['name']}: {str(e)}",
					"Trial Expiry Error"
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			f"Trial expiry check failed: {str(e)}\n{frappe.get_traceback()}",
			"Trial Expiry Check Error"
		)


def send_renewal_reminders():
	"""
	Send renewal reminders for subscriptions expiring soon
	Runs daily
	"""
	try:
		today = getdate(nowdate())

		# Find subscriptions expiring in 7 days
		reminder_date_7 = add_days(today, 7)
		reminder_date_3 = add_days(today, 3)
		reminder_date_1 = add_days(today, 1)

		for reminder_days in [7, 3, 1]:
			reminder_date = add_days(today, reminder_days)

			subscriptions = frappe.get_all(
				'SaaS Subscriptions',
				filters={
					'status': 'Active',
					'end_date': reminder_date,
					'auto_renew': 1
				},
				fields=['name', 'customer_id', 'plan_name', 'end_date']
			)

			for sub in subscriptions:
				try:
					subscription = frappe.get_doc('SaaS Subscriptions', sub['name'])
					send_renewal_reminder(subscription, days_remaining=reminder_days)
				except Exception as e:
					frappe.log_error(
						f"Failed to send renewal reminder for {sub['name']}: {str(e)}",
						"Renewal Reminder Error"
					)
					continue

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			f"Renewal reminders failed: {str(e)}\n{frappe.get_traceback()}",
			"Renewal Reminder Error"
		)


def process_auto_renewals():
	"""
	Process automatic renewals for subscriptions
	Runs daily
	"""
	try:
		today = getdate(nowdate())

		# Find subscriptions that need auto-renewal
		subscriptions_to_renew = frappe.get_all(
			'SaaS Subscriptions',
			filters={
				'status': ['in', ['Active', 'Past Due']],
				'auto_renew': 1,
				'next_billing_date': ['<=', today]
			},
			fields=['name', 'customer_id', 'plan_name', 'price']
		)

		for sub in subscriptions_to_renew:
			try:
				subscription = frappe.get_doc('SaaS Subscriptions', sub['name'])

				# Create renewal payment intent
				# In production, this would trigger payment gateway
				# For now, just log and notify user
				send_renewal_payment_required(subscription)

				frappe.log_error(
					f"Auto-renewal required for subscription {subscription.name}",
					"Auto-Renewal Process"
				)

			except Exception as e:
				frappe.log_error(
					f"Failed to process auto-renewal for {sub['name']}: {str(e)}",
					"Auto-Renewal Error"
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			f"Auto-renewal process failed: {str(e)}\n{frappe.get_traceback()}",
			"Auto-Renewal Process Error"
		)


def update_license_validation_status():
	"""
	Update license validation status for all licenses
	Runs hourly
	"""
	try:
		# Get all active licenses
		licenses = frappe.get_all(
			'SAAS App Validation',
			filters={'validation_status': 'Active'},
			fields=['name', 'license_expiry_date', 'is_lifetime', 'subscription_id']
		)

		today = getdate(nowdate())

		for lic in licenses:
			try:
				# Check if license has expired
				if not lic['is_lifetime'] and lic['license_expiry_date']:
					if getdate(lic['license_expiry_date']) < today:
						update_license_status(lic['name'], 'Expired')

				# Check subscription status
				if lic['subscription_id']:
					subscription_status = frappe.db.get_value('SaaS Subscriptions', lic['subscription_id'], 'status')

					if subscription_status in ['Cancelled', 'Expired', 'Suspended']:
						update_license_status(lic['name'], subscription_status)

			except Exception as e:
				frappe.log_error(
					f"Failed to update license {lic['name']}: {str(e)}",
					"License Validation Update Error"
				)
				continue

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(
			f"License validation update failed: {str(e)}\n{frappe.get_traceback()}",
			"License Validation Update Error"
		)


# Helper functions

def update_license_status(license_key, status):
	"""Update license validation status"""
	try:
		if frappe.db.exists('SaaS App Validation', license_key):
			license_doc = frappe.get_doc('SaaS App Validation', license_key)
			license_doc.validation_status = status
			license_doc.save(ignore_permissions=True)
	except Exception as e:
		frappe.log_error(f"Failed to update license status: {str(e)}", "License Status Update")


def send_renewal_reminder(subscription, days_remaining=None):
	"""Send renewal reminder email"""
	try:
		# Get customer email
		customer_email = frappe.db.get_value('User', subscription.customer_id, 'email')

		if not customer_email:
			return

		# Prepare email content
		if days_remaining:
			subject = f"Your subscription will expire in {days_remaining} day{'s' if days_remaining > 1 else ''}"
			message = f"""
				Your subscription for {subscription.plan_name} will expire in {days_remaining} day{'s' if days_remaining > 1 else ''}.

				Subscription Details:
				- Plan: {subscription.plan_name}
				- End Date: {subscription.end_date}
				- Amount: {subscription.price}

				Please ensure your payment is processed to continue enjoying our services.
			"""
		else:
			subject = "Your subscription has expired"
			message = f"""
				Your subscription for {subscription.plan_name} has expired.

				Please renew your subscription to continue using our services.
			"""

		frappe.sendmail(
			recipients=[customer_email],
			subject=subject,
			message=message
		)

	except Exception as e:
		frappe.log_error(f"Failed to send renewal reminder: {str(e)}", "Renewal Reminder Email")


def send_expiry_notification(subscription):
	"""Send subscription expiry notification"""
	try:
		customer_email = frappe.db.get_value('User', subscription.customer_id, 'email')

		if not customer_email:
			return

		frappe.sendmail(
			recipients=[customer_email],
			subject=f"Your subscription for {subscription.plan_name} has expired",
			message=f"""
				Your subscription has expired.

				Subscription Details:
				- Plan: {subscription.plan_name}
				- Expired On: {subscription.end_date}

				To continue using our services, please purchase a new subscription.
			"""
		)

	except Exception as e:
		frappe.log_error(f"Failed to send expiry notification: {str(e)}", "Expiry Notification Email")


def send_trial_expiry_notification(subscription):
	"""Send trial expiry notification"""
	try:
		customer_email = frappe.db.get_value('User', subscription.customer_id, 'email')

		if not customer_email:
			return

		frappe.sendmail(
			recipients=[customer_email],
			subject=f"Your trial period for {subscription.plan_name} has ended",
			message=f"""
				Your trial period has ended.

				To continue using {subscription.plan_name}, please complete your payment.
			"""
		)

	except Exception as e:
		frappe.log_error(f"Failed to send trial expiry notification: {str(e)}", "Trial Expiry Notification Email")


def send_renewal_payment_required(subscription):
	"""Send renewal payment required notification"""
	try:
		customer_email = frappe.db.get_value('User', subscription.customer_id, 'email')

		if not customer_email:
			return

		frappe.sendmail(
			recipients=[customer_email],
			subject=f"Payment required for subscription renewal",
			message=f"""
				Your subscription is due for renewal.

				Subscription Details:
				- Plan: {subscription.plan_name}
				- Amount: {subscription.price}
				- Next Billing Date: {subscription.next_billing_date}

				Please complete the payment to continue your subscription.
			"""
		)

	except Exception as e:
		frappe.log_error(f"Failed to send renewal payment notification: {str(e)}", "Renewal Payment Notification Email")
