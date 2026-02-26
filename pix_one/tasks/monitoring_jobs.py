"""
Background jobs for monitoring, health checks, and usage snapshots.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


def check_platform_health():
    """Hourly platform health check and alert generation."""
    try:
        # Check for failed sites
        failed_companies = frappe.get_all("SaaS Company", {
            "status": "Failed"
        }, ["name", "company_name", "site_name"])

        if failed_companies:
            _create_alert(
                "failed_sites",
                "warning",
                f"{len(failed_companies)} site(s) in failed state"
            )

        # Check disk usage
        import shutil
        total, used, free = shutil.disk_usage("/")
        usage_pct = (used / total) * 100

        if usage_pct > 90:
            _create_alert("disk_usage", "critical", f"Disk usage at {usage_pct:.1f}%")
        elif usage_pct > 80:
            _create_alert("disk_usage", "warning", f"Disk usage at {usage_pct:.1f}%")

        # Check failed background jobs
        failed_jobs = frappe.db.count("RQ Job", {
            "status": "failed",
            "creation": [">=", frappe.utils.add_to_date(now_datetime(), hours=-1)]
        })

        if failed_jobs > 10:
            _create_alert(
                "failed_jobs",
                "warning",
                f"{failed_jobs} failed jobs in the last hour"
            )

    except Exception as e:
        frappe.log_error(str(e), "Health Check Error")


def take_usage_snapshots():
    """Daily usage snapshot for trend tracking."""
    try:
        subscriptions = frappe.get_all("SaaS Subscriptions", {
            "status": ["in", ["Active", "Trial"]]
        }, ["name", "current_users", "current_storage_mb"])

        for sub in subscriptions:
            active_companies = frappe.db.count("SaaS Company", {
                "subscription_id": sub.name,
                "status": ["not in", ["Deleted", "Failed"]]
            })

            frappe.get_doc({
                "doctype": "SaaS Audit Log",
                "action": "usage_snapshot",
                "user": "Administrator",
                "reference_doctype": "SaaS Subscriptions",
                "reference_name": sub.name,
                "data": frappe.as_json({
                    "companies": active_companies,
                    "users": sub.current_users or 0,
                    "storage_mb": sub.current_storage_mb or 0
                })
            }).insert(ignore_permissions=True)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(str(e), "Usage Snapshot Error")


def process_scheduled_downgrades():
    """Process subscriptions scheduled for plan downgrade."""
    try:
        from frappe.utils import today

        subs = frappe.get_all("SaaS Subscriptions", {
            "scheduled_plan_change": ["is", "set"],
            "scheduled_change_date": ["<=", today()],
            "status": "Active"
        }, ["name", "scheduled_plan_change"])

        for sub_data in subs:
            try:
                sub = frappe.get_doc("SaaS Subscriptions", sub_data.name)
                new_plan = sub.scheduled_plan_change

                sub.plan_name = new_plan
                plan = frappe.get_doc("SaaS Subscription Plan", new_plan)
                sub.price = plan.price
                sub.scheduled_plan_change = None
                sub.scheduled_change_date = None
                sub.save(ignore_permissions=True)

                frappe.get_doc({
                    "doctype": "SaaS Audit Log",
                    "action": "plan_downgraded",
                    "user": sub.customer_id,
                    "reference_doctype": "SaaS Subscriptions",
                    "reference_name": sub.name,
                    "data": frappe.as_json({"new_plan": new_plan})
                }).insert(ignore_permissions=True)

            except Exception as e:
                frappe.log_error(
                    f"Downgrade failed for {sub_data.name}: {str(e)}",
                    "Scheduled Downgrade Error"
                )

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(str(e), "Process Downgrades Error")


def cleanup_expired_invites():
    """Clean up expired team invitations."""
    try:
        from frappe.utils import today
        frappe.db.sql("""
            UPDATE `tabSaaS Team Member`
            SET status = 'Expired'
            WHERE status = 'Invited'
              AND invite_expires_at < %s
        """, today())
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(str(e), "Invite Cleanup Error")


def _create_alert(alert_type, severity, message):
    """Create or update an alert."""
    existing = frappe.db.exists("SaaS Alert Rule", {"alert_type": alert_type, "is_active": 1})
    if existing:
        frappe.db.set_value("SaaS Alert Rule", existing, {
            "last_triggered": now_datetime(),
            "trigger_count": frappe.db.get_value("SaaS Alert Rule", existing, "trigger_count") + 1,
            "message": message
        })
    else:
        frappe.get_doc({
            "doctype": "SaaS Alert Rule",
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "is_active": 1,
            "last_triggered": now_datetime(),
            "trigger_count": 1
        }).insert(ignore_permissions=True)
