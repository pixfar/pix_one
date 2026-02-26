"""
Module 3: Subscriptions - Usage & Invoices Endpoints
"""

import frappe
from frappe import _
from frappe.utils import flt
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


@frappe.whitelist()
@handle_exceptions
def get_usage(subscription_id):
    """Get current usage vs limits for a subscription."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your subscription"))

    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    active_companies = frappe.db.count("SaaS Company", {
        "subscription_id": subscription_id,
        "status": ["not in", ["Deleted", "Failed"]]
    })

    return ResponseFormatter.success(data={
        "subscription_id": sub.name,
        "plan": plan.plan_name,
        "usage": {
            "companies": {"current": active_companies, "max": plan.max_companies or 1},
            "users": {"current": sub.current_users or 0, "max": plan.max_users or 5},
            "storage_mb": {"current": flt(sub.current_storage_mb), "max": plan.max_storage_mb or 1024},
        },
        "percentages": {
            "companies": round((active_companies / max(plan.max_companies or 1, 1)) * 100, 1),
            "users": round(((sub.current_users or 0) / max(plan.max_users or 5, 1)) * 100, 1),
            "storage": round((flt(sub.current_storage_mb) / max(plan.max_storage_mb or 1024, 1)) * 100, 1),
        }
    })


@frappe.whitelist()
@handle_exceptions
def get_usage_history(subscription_id, period="30d"):
    """Get usage trends over time for a subscription."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your subscription"))

    # Get audit log entries for usage tracking
    days = 30 if period == "30d" else (7 if period == "7d" else 90)

    history = frappe.db.sql("""
        SELECT DATE(creation) as date,
               JSON_EXTRACT(data, '$.companies') as companies,
               JSON_EXTRACT(data, '$.users') as users,
               JSON_EXTRACT(data, '$.storage_mb') as storage_mb
        FROM `tabSaaS Audit Log`
        WHERE reference_doctype = 'SaaS Subscriptions'
          AND reference_name = %s
          AND action = 'usage_snapshot'
          AND creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
        ORDER BY creation ASC
    """, (subscription_id, days), as_dict=True)

    return ResponseFormatter.success(data={"period": period, "history": history})


@frappe.whitelist()
@handle_exceptions
def get_invoices(subscription_id=None, page=1, limit=20):
    """Get billing invoices for a subscription or all user invoices."""
    user = frappe.session.user
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {"customer_id": user, "status": "Completed"}
    if subscription_id:
        sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
        if sub.customer_id != user:
            return ResponseFormatter.forbidden(_("Not your subscription"))
        filters["subscription_id"] = subscription_id

    invoices = frappe.get_all(
        "SaaS Payment Transaction",
        filters=filters,
        fields=[
            "name", "transaction_id", "amount", "currency", "payment_date",
            "transaction_type", "payment_method", "subscription_id",
            "billing_period_start", "billing_period_end"
        ],
        order_by="payment_date desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS Payment Transaction", filters)

    return ResponseFormatter.paginated(data=invoices, total=total, page=page, limit=limit)


@frappe.whitelist()
@handle_exceptions
def download_invoice(transaction_id):
    """Download a PDF invoice for a payment transaction."""
    user = frappe.session.user
    txn = frappe.get_doc("SaaS Payment Transaction", transaction_id)

    if txn.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your transaction"))

    # Generate print format URL
    pdf_url = f"/api/method/frappe.utils.print_format.download_pdf?doctype=SaaS Payment Transaction&name={transaction_id}&format=Standard"

    return ResponseFormatter.success(data={
        "transaction_id": txn.name,
        "amount": txn.amount,
        "currency": txn.currency,
        "download_url": pdf_url
    })
