"""
Module 7: License & Compliance - Extended License, Usage Alerts, GDPR
"""

import frappe
from frappe import _
from frappe.utils import flt
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


@frappe.whitelist()
@handle_exceptions
def get_resource_usage(license_key=None, subscription_id=None):
    """Get current resource consumption for a license."""
    user = frappe.session.user

    filters = {}
    if license_key:
        filters["license_key"] = license_key
    elif subscription_id:
        filters["subscription_id"] = subscription_id
    else:
        # Find user's active license
        sub = frappe.db.get_value("SaaS Subscriptions", {
            "customer_id": user, "status": "Active"
        }, "name")
        if not sub:
            return ResponseFormatter.not_found(_("No active subscription found"))
        filters["subscription_id"] = sub

    validation = frappe.get_all("SaaS App Validation", filters=filters, limit=1)
    if not validation:
        return ResponseFormatter.not_found(_("No license validation record found"))

    doc = frappe.get_doc("SaaS App Validation", validation[0].name)

    return ResponseFormatter.success(data={
        "license_key": doc.license_key,
        "status": doc.validation_status,
        "resources": {
            "users": {"current": doc.current_users or 0, "max": doc.max_users or 0},
            "storage_mb": {"current": flt(doc.current_storage_mb), "max": doc.max_storage_mb or 0},
            "companies": {"current": doc.current_companies or 0, "max": doc.max_companies or 0},
        },
        "violations": {
            "count": doc.violation_count or 0,
            "details": doc.get("violation_details")
        },
        "last_check": doc.last_validation_check,
        "access_count": doc.access_count or 0
    })


@frappe.whitelist()
@handle_exceptions
def get_usage_alerts(subscription_id=None):
    """Get usage threshold alerts for the user's subscription."""
    user = frappe.session.user

    if not subscription_id:
        subscription_id = frappe.db.get_value("SaaS Subscriptions", {
            "customer_id": user, "status": "Active"
        }, "name")

    if not subscription_id:
        return ResponseFormatter.not_found(_("No active subscription"))

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your subscription"))

    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    alerts = []
    active_companies = frappe.db.count("SaaS Company", {
        "subscription_id": subscription_id, "status": ["not in", ["Deleted", "Failed"]]
    })

    # Check company usage
    max_companies = plan.max_companies or 1
    if active_companies >= max_companies:
        alerts.append({"type": "companies", "level": "critical", "message": "Company limit reached"})
    elif active_companies >= max_companies * 0.8:
        alerts.append({"type": "companies", "level": "warning", "message": "80% of company limit used"})

    # Check user usage
    max_users = plan.max_users or 5
    current_users = sub.current_users or 0
    if current_users >= max_users:
        alerts.append({"type": "users", "level": "critical", "message": "User limit reached"})
    elif current_users >= max_users * 0.8:
        alerts.append({"type": "users", "level": "warning", "message": "80% of user limit used"})

    # Check storage usage
    max_storage = plan.max_storage_mb or 1024
    current_storage = flt(sub.current_storage_mb)
    if current_storage >= max_storage:
        alerts.append({"type": "storage", "level": "critical", "message": "Storage limit reached"})
    elif current_storage >= max_storage * 0.8:
        alerts.append({"type": "storage", "level": "warning", "message": "80% of storage used"})

    return ResponseFormatter.success(data={"alerts": alerts, "subscription_id": subscription_id})


@frappe.whitelist()
@handle_exceptions
def set_usage_alerts(subscription_id, thresholds):
    """Configure usage alert thresholds."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    import json
    if isinstance(thresholds, str):
        thresholds = json.loads(thresholds)

    cache_key = f"usage_alert_thresholds:{subscription_id}"
    frappe.cache().set_value(cache_key, thresholds, expires_in_sec=365 * 24 * 3600)

    return ResponseFormatter.success(message=_("Alert thresholds updated"))


@frappe.whitelist()
@handle_exceptions
def get_compliance_report(subscription_id=None):
    """Get GDPR/data compliance report."""
    user = frappe.session.user

    if not subscription_id:
        subscription_id = frappe.db.get_value("SaaS Subscriptions", {
            "customer_id": user, "status": ["in", ["Active", "Trial"]]
        }, "name")

    if not subscription_id:
        return ResponseFormatter.not_found(_("No active subscription"))

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your subscription"))

    # Collect data inventory
    companies = frappe.get_all("SaaS Company", {
        "subscription_id": subscription_id
    }, ["name", "company_name", "site_name", "creation"])

    transactions = frappe.db.count("SaaS Payment Transaction", {
        "subscription_id": subscription_id
    })

    return ResponseFormatter.success(data={
        "subscription_id": subscription_id,
        "data_inventory": {
            "companies": len(companies),
            "payment_transactions": transactions,
            "user_email": user,
        },
        "companies": companies,
        "data_retention_policy": "Data is retained for 90 days after subscription cancellation",
        "compliance_features": [
            "Data encryption at rest",
            "Data encryption in transit (TLS 1.3)",
            "Right to data export",
            "Right to data deletion",
            "Audit logging enabled"
        ]
    })


@frappe.whitelist()
@handle_exceptions
def request_data_export(subscription_id=None):
    """Request export of all tenant data (GDPR Right to Portability)."""
    user = frappe.session.user

    if not subscription_id:
        subscription_id = frappe.db.get_value("SaaS Subscriptions", {
            "customer_id": user, "status": ["in", ["Active", "Trial", "Expired"]]
        }, "name")

    if not subscription_id:
        return ResponseFormatter.not_found(_("No subscription found"))

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    # Enqueue export job
    frappe.enqueue(
        "pix_one.tasks.compliance_jobs.export_user_data",
        queue="long",
        timeout=600,
        user=user,
        subscription_id=subscription_id,
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(
        message=_("Data export request submitted. You will receive a download link via email.")
    )


@frappe.whitelist()
@handle_exceptions
def request_data_deletion(subscription_id=None, confirmation=""):
    """Request deletion of all tenant data (GDPR Right to Erasure)."""
    user = frappe.session.user

    if confirmation != "DELETE_MY_DATA":
        return ResponseFormatter.validation_error(
            _("To confirm deletion, pass confirmation='DELETE_MY_DATA'")
        )

    if not subscription_id:
        subscription_id = frappe.db.get_value("SaaS Subscriptions", {
            "customer_id": user
        }, "name", order_by="creation desc")

    if not subscription_id:
        return ResponseFormatter.not_found(_("No subscription found"))

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    # Schedule deletion (with 30-day grace period)
    from frappe.utils import add_days, today
    deletion_date = add_days(today(), 30)

    frappe.cache().set_value(f"data_deletion_request:{user}", {
        "subscription_id": subscription_id,
        "requested_at": str(frappe.utils.now_datetime()),
        "scheduled_deletion_date": str(deletion_date)
    }, expires_in_sec=35 * 24 * 3600)

    return ResponseFormatter.success(data={
        "scheduled_deletion_date": str(deletion_date),
        "message": _("Your data will be permanently deleted on {0}. "
                     "You can cancel this request within 30 days.").format(deletion_date)
    })
