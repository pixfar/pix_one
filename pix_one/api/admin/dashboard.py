"""
Module 8: Admin Dashboard - Platform Operations & Analytics
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, today, now_datetime
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


def _require_admin():
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Admin access required"), frappe.PermissionError)


@frappe.whitelist()
@handle_exceptions
def get_overview():
    """Get platform KPIs: MRR, ARR, churn, growth."""
    _require_admin()

    active_subs = frappe.db.count("SaaS Subscriptions", {"status": "Active"})
    trial_subs = frappe.db.count("SaaS Subscriptions", {"status": "Trial"})
    expired_subs = frappe.db.count("SaaS Subscriptions", {"status": "Expired"})
    cancelled_subs = frappe.db.count("SaaS Subscriptions", {"status": "Cancelled"})
    total_companies = frappe.db.count("SaaS Company", {"status": ["not in", ["Deleted", "Failed"]]})
    total_users = frappe.db.count("User", {"user_type": "Website User", "enabled": 1})

    # MRR calculation
    mrr_result = frappe.db.sql("""
        SELECT COALESCE(SUM(
            CASE
                WHEN sp.billing_interval = 'Monthly' THEN sp.price
                WHEN sp.billing_interval = 'Quarterly' THEN sp.price / 3
                WHEN sp.billing_interval = 'Yearly' THEN sp.price / 12
                ELSE 0
            END
        ), 0) as mrr
        FROM `tabSaaS Subscriptions` s
        JOIN `tabSaaS Subscription Plan` sp ON s.plan_name = sp.name
        WHERE s.status = 'Active'
    """, as_dict=True)
    mrr = flt(mrr_result[0].mrr if mrr_result else 0, 2)

    # Revenue this month
    month_revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM `tabSaaS Payment Transaction`
        WHERE status = 'Completed'
          AND MONTH(payment_date) = MONTH(NOW())
          AND YEAR(payment_date) = YEAR(NOW())
    """, as_dict=True)[0].total

    # Churn rate (last 30 days)
    start_of_period = add_days(today(), -30)
    cancelled_in_period = frappe.db.count("SaaS Subscriptions", {
        "status": "Cancelled",
        "cancellation_date": [">=", start_of_period]
    })
    active_at_start = active_subs + cancelled_in_period
    churn_rate = round((cancelled_in_period / max(active_at_start, 1)) * 100, 2)

    return ResponseFormatter.success(data={
        "subscriptions": {
            "active": active_subs,
            "trial": trial_subs,
            "expired": expired_subs,
            "cancelled": cancelled_subs,
            "total": active_subs + trial_subs + expired_subs + cancelled_subs
        },
        "revenue": {
            "mrr": mrr,
            "arr": round(mrr * 12, 2),
            "this_month": flt(month_revenue, 2)
        },
        "metrics": {
            "churn_rate_30d": churn_rate,
            "total_companies": total_companies,
            "total_users": total_users,
        }
    })


@frappe.whitelist()
@handle_exceptions
def get_revenue_chart(period="12m"):
    """Get revenue over time for charts."""
    _require_admin()

    months = 12 if period == "12m" else (6 if period == "6m" else 3)

    data = frappe.db.sql("""
        SELECT DATE_FORMAT(payment_date, '%%Y-%%m') as month,
               SUM(amount) as revenue,
               COUNT(*) as transactions
        FROM `tabSaaS Payment Transaction`
        WHERE status = 'Completed'
          AND payment_date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
        GROUP BY DATE_FORMAT(payment_date, '%%Y-%%m')
        ORDER BY month ASC
    """, months, as_dict=True)

    return ResponseFormatter.success(data=data)


@frappe.whitelist()
@handle_exceptions
def get_subscription_stats():
    """Get subscription status distribution over time."""
    _require_admin()

    stats = frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tabSaaS Subscriptions`
        GROUP BY status
        ORDER BY count DESC
    """, as_dict=True)

    # Plan distribution
    plan_dist = frappe.db.sql("""
        SELECT sp.plan_name, COUNT(s.name) as subscribers
        FROM `tabSaaS Subscriptions` s
        JOIN `tabSaaS Subscription Plan` sp ON s.plan_name = sp.name
        WHERE s.status = 'Active'
        GROUP BY sp.plan_name
        ORDER BY subscribers DESC
    """, as_dict=True)

    return ResponseFormatter.success(data={
        "status_distribution": stats,
        "plan_distribution": plan_dist
    })


@frappe.whitelist()
@handle_exceptions
def get_signup_funnel():
    """Get signup → trial → paid conversion funnel."""
    _require_admin()

    total_signups = frappe.db.count("User", {"user_type": "Website User"})
    total_trials = frappe.db.count("SaaS Subscriptions", {"status": ["in", ["Trial", "Active", "Expired", "Cancelled"]]})
    total_paid = frappe.db.count("SaaS Subscriptions", {"status": ["in", ["Active", "Expired"]], "total_amount_paid": [">", 0]})

    return ResponseFormatter.success(data={
        "funnel": [
            {"stage": "Signups", "count": total_signups, "rate": 100},
            {"stage": "Trials Started", "count": total_trials, "rate": round((total_trials / max(total_signups, 1)) * 100, 1)},
            {"stage": "Paid Conversions", "count": total_paid, "rate": round((total_paid / max(total_trials, 1)) * 100, 1)},
        ]
    })


# ==================== TENANT MANAGEMENT ====================

@frappe.whitelist()
@handle_exceptions
def list_tenants(page=1, limit=20, status=None, search=None):
    """List all tenants with filters."""
    _require_admin()
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {}
    if status:
        filters["status"] = status

    or_filters = None
    if search:
        or_filters = [
            ["customer_id", "like", f"%{search}%"],
            ["plan_name", "like", f"%{search}%"]
        ]

    subs = frappe.get_all(
        "SaaS Subscriptions",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name", "customer_id", "plan_name", "status", "start_date",
            "end_date", "price", "auto_renew", "creation", "current_users"
        ],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS Subscriptions", filters)

    return ResponseFormatter.paginated(data=subs, total=total, page=page, limit=limit)


@frappe.whitelist()
@handle_exceptions
def get_tenant_details(subscription_id):
    """Get full tenant details including usage and billing."""
    _require_admin()

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    companies = frappe.get_all("SaaS Company", {
        "subscription_id": subscription_id
    }, ["name", "company_name", "site_name", "status", "creation"])

    transactions = frappe.get_all("SaaS Payment Transaction", {
        "subscription_id": subscription_id
    }, ["name", "amount", "status", "payment_date", "transaction_type"], order_by="creation desc", limit=10)

    return ResponseFormatter.success(data={
        "subscription": {
            "id": sub.name,
            "customer_id": sub.customer_id,
            "plan": plan.plan_name,
            "status": sub.status,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "auto_renew": sub.auto_renew,
            "price": sub.price,
            "total_paid": sub.total_amount_paid,
        },
        "usage": {
            "companies": len(companies),
            "max_companies": plan.max_companies,
            "users": sub.current_users or 0,
            "max_users": plan.max_users,
        },
        "companies": companies,
        "recent_transactions": transactions
    })


@frappe.whitelist()
@handle_exceptions
def impersonate_tenant(subscription_id):
    """Generate a temporary admin login URL for a tenant's site (Admin only)."""
    _require_admin()

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    company = frappe.get_all("SaaS Company", {
        "subscription_id": subscription_id, "status": "Active"
    }, ["site_url", "admin_email"], limit=1)

    if not company:
        return ResponseFormatter.not_found(_("No active company/site found"))

    # Log this action for audit
    frappe.get_doc({
        "doctype": "SaaS Audit Log",
        "action": "admin_impersonation",
        "user": frappe.session.user,
        "reference_doctype": "SaaS Subscriptions",
        "reference_name": subscription_id,
        "data": frappe.as_json({"target_user": sub.customer_id})
    }).insert(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "site_url": company[0].site_url,
        "admin_email": company[0].admin_email,
        "message": _("Use the admin credentials to access the tenant site. This action has been logged.")
    })


@frappe.whitelist()
@handle_exceptions
def send_announcement(subject, message, filter_status=None):
    """Send announcement to all or filtered tenants."""
    _require_admin()

    filters = {"user_type": "Website User", "enabled": 1}
    if filter_status:
        # Get users with specific subscription status
        user_emails = frappe.db.sql("""
            SELECT DISTINCT customer_id FROM `tabSaaS Subscriptions`
            WHERE status = %s
        """, filter_status, as_list=True)
        user_emails = [u[0] for u in user_emails]
    else:
        user_emails = frappe.get_all("User", filters, pluck="name")

    if not user_emails:
        return ResponseFormatter.validation_error(_("No recipients found"))

    # Send in batches
    frappe.enqueue(
        "pix_one.tasks.notification_jobs.send_bulk_email",
        queue="short",
        recipients=user_emails,
        subject=subject,
        message=message,
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(data={
        "recipients_count": len(user_emails),
        "message": _("Announcement queued for {0} recipients").format(len(user_emails))
    })


@frappe.whitelist()
@handle_exceptions
def suspend_tenant(subscription_id, reason=None):
    """Suspend a tenant for policy violation (Admin only)."""
    _require_admin()

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    sub.status = "Suspended"
    sub.save(ignore_permissions=True)

    # Suspend all companies
    companies = frappe.get_all("SaaS Company", {"subscription_id": subscription_id, "status": "Active"})
    for c in companies:
        frappe.db.set_value("SaaS Company", c.name, "status", "Suspended")

    # Log audit
    frappe.get_doc({
        "doctype": "SaaS Audit Log",
        "action": "tenant_suspended",
        "user": frappe.session.user,
        "reference_doctype": "SaaS Subscriptions",
        "reference_name": subscription_id,
        "data": frappe.as_json({"reason": reason or "Policy violation"})
    }).insert(ignore_permissions=True)

    frappe.db.commit()

    return ResponseFormatter.success(message=_("Tenant suspended"))


# ==================== HEALTH & SUPPORT ====================

@frappe.whitelist()
@handle_exceptions
def get_cluster_health():
    """Get overall health of all sites."""
    _require_admin()

    companies = frappe.get_all("SaaS Company", {"status": "Active"}, ["name", "site_name", "company_name"])

    return ResponseFormatter.success(data={
        "total_active_sites": len(companies),
        "sites": [{"company_id": c.name, "site_name": c.site_name, "company_name": c.company_name} for c in companies]
    })


@frappe.whitelist()
@handle_exceptions
def get_failed_jobs():
    """Get failed background jobs."""
    _require_admin()

    jobs = frappe.db.sql("""
        SELECT name, job_name, status, exc, creation
        FROM `tabRQ Job`
        WHERE status = 'failed'
        ORDER BY creation DESC
        LIMIT 50
    """, as_dict=True)

    return ResponseFormatter.success(data=jobs)


@frappe.whitelist()
@handle_exceptions
def restart_site(company_id):
    """Restart a tenant site (Admin only)."""
    _require_admin()

    doc = frappe.get_doc("SaaS Company", company_id)
    # This would trigger a site restart via bench
    # In production, this would interact with the orchestration layer

    return ResponseFormatter.success(message=_("Site restart requested for {0}").format(doc.site_name))


# ==================== AUDIT ====================

@frappe.whitelist()
@handle_exceptions
def get_audit_log(page=1, limit=50, action=None, user=None):
    """Get platform-wide audit log."""
    _require_admin()
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {}
    if action:
        filters["action"] = action
    if user:
        filters["user"] = user

    logs = frappe.get_all(
        "SaaS Audit Log",
        filters=filters,
        fields=["name", "action", "user", "reference_doctype", "reference_name", "data", "creation"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS Audit Log", filters)

    return ResponseFormatter.paginated(data=logs, total=total, page=page, limit=limit)


@frappe.whitelist()
@handle_exceptions
def get_security_events(page=1, limit=50):
    """Get security events (failed logins, suspicious activity)."""
    _require_admin()
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    events = frappe.get_all(
        "Activity Log",
        filters={"status": "Failed"},
        fields=["name", "subject", "user", "operation", "ip_address", "creation"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("Activity Log", {"status": "Failed"})

    return ResponseFormatter.paginated(data=events, total=total, page=page, limit=limit)
