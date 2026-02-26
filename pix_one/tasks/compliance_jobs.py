"""
Background jobs for GDPR compliance (data export, data deletion).
"""

import frappe
from frappe import _
import json


def export_user_data(user, subscription_id):
    """Export all user data for GDPR compliance."""
    try:
        data = {
            "user_info": frappe.get_doc("User", user).as_dict(),
            "subscriptions": frappe.get_all(
                "SaaS Subscriptions",
                filters={"customer_id": user},
                fields=["*"]
            ),
            "companies": frappe.get_all(
                "SaaS Company",
                filters={"customer_id": user},
                fields=["*"]
            ),
            "transactions": frappe.get_all(
                "SaaS Payment Transaction",
                filters={"customer_id": user},
                fields=["*"]
            ),
        }

        # Save as file
        file_content = json.dumps(data, default=str, indent=2)
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": f"data_export_{user}_{frappe.utils.now_datetime().strftime('%Y%m%d')}.json",
            "content": file_content,
            "is_private": 1
        })
        file_doc.insert(ignore_permissions=True)

        # Notify user
        frappe.sendmail(
            recipients=[user],
            subject=_("Your Data Export is Ready"),
            message=_("Your data export has been generated. "
                      "You can download it from your dashboard."),
            now=True
        )

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(
            f"Data export failed for {user}: {str(e)}",
            "GDPR Export Error"
        )
