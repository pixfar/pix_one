"""
Module 3: Subscriptions - Upgrade/Downgrade Endpoints
"""

import frappe
from frappe import _
from frappe.utils import getdate, date_diff, add_days, today, nowdate, flt
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


def _get_proration_amount(current_plan, new_plan, days_remaining, total_days):
    """Calculate prorated amount for plan change."""
    if total_days <= 0:
        return 0, 0

    daily_rate_current = flt(current_plan.price) / total_days
    daily_rate_new = flt(new_plan.price) / total_days

    credit = daily_rate_current * days_remaining
    charge = daily_rate_new * days_remaining
    amount_due = max(0, charge - credit)

    return flt(amount_due, 2), flt(credit, 2)


@frappe.whitelist()
@handle_exceptions
def preview_upgrade(subscription_id, new_plan_id):
    """Preview the cost of upgrading or downgrading a subscription."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    if sub.status not in ("Active", "Trial"):
        return ResponseFormatter.validation_error(_("Only active subscriptions can be changed"))

    current_plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)
    new_plan = frappe.get_doc("SaaS Subscription Plan", new_plan_id)

    if not new_plan.is_active:
        return ResponseFormatter.validation_error(_("Target plan is not available"))

    # Calculate proration
    end_date = getdate(sub.end_date) if sub.end_date else getdate(today())
    start_date = getdate(sub.start_date) if sub.start_date else getdate(today())
    total_days = max(date_diff(end_date, start_date), 1)
    days_remaining = max(date_diff(end_date, getdate(today())), 0)

    amount_due, credit = _get_proration_amount(current_plan, new_plan, days_remaining, total_days)

    is_upgrade = flt(new_plan.price) > flt(current_plan.price)

    return ResponseFormatter.success(data={
        "current_plan": {"name": current_plan.plan_name, "price": current_plan.price},
        "new_plan": {"name": new_plan.plan_name, "price": new_plan.price},
        "is_upgrade": is_upgrade,
        "days_remaining": days_remaining,
        "credit_amount": credit,
        "amount_due": amount_due if is_upgrade else 0,
        "effective": "immediately" if is_upgrade else "end_of_billing_period",
        "new_billing_amount": new_plan.price,
    })


@frappe.whitelist()
@handle_exceptions
def upgrade_subscription(subscription_id, new_plan_id):
    """Upgrade a subscription to a higher plan (effective immediately with proration)."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    if sub.status not in ("Active", "Trial"):
        return ResponseFormatter.validation_error(_("Only active subscriptions can be upgraded"))

    new_plan = frappe.get_doc("SaaS Subscription Plan", new_plan_id)
    current_plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    if flt(new_plan.price) <= flt(current_plan.price):
        return ResponseFormatter.validation_error(_("New plan must be higher priced. Use downgrade instead."))

    # Calculate proration
    end_date = getdate(sub.end_date) if sub.end_date else getdate(today())
    start_date = getdate(sub.start_date) if sub.start_date else getdate(today())
    total_days = max(date_diff(end_date, start_date), 1)
    days_remaining = max(date_diff(end_date, getdate(today())), 0)
    amount_due, credit = _get_proration_amount(current_plan, new_plan, days_remaining, total_days)

    # Update subscription
    sub.plan_name = new_plan_id
    sub.price = new_plan.price
    sub.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "subscription_id": sub.name,
        "new_plan": new_plan.plan_name,
        "amount_due": amount_due,
        "credit_applied": credit,
        "effective_immediately": True
    }, message=_("Subscription upgraded successfully"))


@frappe.whitelist()
@handle_exceptions
def downgrade_subscription(subscription_id, new_plan_id):
    """Downgrade a subscription (effective at end of current billing period)."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    if sub.status != "Active":
        return ResponseFormatter.validation_error(_("Only active subscriptions can be downgraded"))

    new_plan = frappe.get_doc("SaaS Subscription Plan", new_plan_id)
    current_plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    if flt(new_plan.price) >= flt(current_plan.price):
        return ResponseFormatter.validation_error(_("New plan must be lower priced. Use upgrade instead."))

    # Validate company limits
    active_companies = frappe.db.count("SaaS Company", {
        "subscription_id": subscription_id,
        "status": ["not in", ["Deleted", "Failed"]]
    })
    if active_companies > (new_plan.max_companies or 1):
        return ResponseFormatter.validation_error(
            _("You have {0} active companies but the new plan only allows {1}. "
              "Please delete some companies first.").format(active_companies, new_plan.max_companies)
        )

    # Schedule downgrade at end of period
    sub.db_set("scheduled_plan_change", new_plan_id, update_modified=False)
    sub.db_set("scheduled_change_date", sub.end_date, update_modified=False)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "subscription_id": sub.name,
        "new_plan": new_plan.plan_name,
        "effective_date": str(sub.end_date),
        "effective_immediately": False,
        "message": _("Downgrade scheduled for end of billing period")
    })
