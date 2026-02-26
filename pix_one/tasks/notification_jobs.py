"""
Background jobs for notifications and email campaigns.
"""

import frappe
from frappe import _


def send_bulk_email(recipients, subject, message):
    """Send bulk email to a list of recipients."""
    for email in recipients:
        try:
            frappe.sendmail(
                recipients=[email],
                subject=subject,
                message=message,
                now=False  # Queue for sending
            )
        except Exception:
            frappe.log_error(
                f"Failed to send email to {email}",
                "Bulk Email Error"
            )

    frappe.db.commit()
