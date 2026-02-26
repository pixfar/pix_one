"""
Module 2: Subscription Plans - Admin Management Endpoints
"""

import frappe
from frappe import _
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


def _require_admin():
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Admin access required"), frappe.PermissionError)


@frappe.whitelist()
@handle_exceptions
def create_plan(
    plan_name, plan_code, price, billing_interval="Monthly",
    currency="USD", setup_fee=0, max_companies=1, max_users=5,
    max_storage_mb=1024, description=None, allow_trial=0,
    trial_period_days=0, sort_order=0, features=None
):
    """Create a new subscription plan (Admin only)."""
    _require_admin()

    if frappe.db.exists("SaaS Subscription Plan", {"plan_code": plan_code}):
        return ResponseFormatter.validation_error(_("Plan code already exists"))

    plan = frappe.get_doc({
        "doctype": "SaaS Subscription Plan",
        "plan_name": plan_name,
        "plan_code": plan_code,
        "price": float(price),
        "currency": currency,
        "setup_fee": float(setup_fee or 0),
        "billing_interval": billing_interval,
        "max_companies": int(max_companies),
        "max_users": int(max_users),
        "max_storage_mb": int(max_storage_mb),
        "description": description,
        "allow_trial": int(allow_trial),
        "trial_period_days": int(trial_period_days or 0),
        "sort_order": int(sort_order or 0),
        "is_active": 0
    })

    if features and isinstance(features, list):
        for feat in features:
            plan.append("features", {
                "feature_name": feat.get("feature_name"),
                "description": feat.get("description", ""),
                "is_included": feat.get("is_included", 1),
                "limit_value": feat.get("limit_value", "")
            })

    plan.insert(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.created(
        data={"plan_id": plan.name, "plan_name": plan.plan_name, "plan_code": plan.plan_code},
        message=_("Subscription plan created")
    )


@frappe.whitelist()
@handle_exceptions
def update_plan(plan_id, **kwargs):
    """Update an existing subscription plan (Admin only)."""
    _require_admin()

    plan = frappe.get_doc("SaaS Subscription Plan", plan_id)

    updatable_fields = [
        "plan_name", "price", "setup_fee", "billing_interval", "currency",
        "max_companies", "max_users", "max_storage_mb", "description",
        "allow_trial", "trial_period_days", "sort_order"
    ]

    for field in updatable_fields:
        if field in kwargs and kwargs[field] is not None:
            plan.set(field, kwargs[field])

    plan.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.updated(
        data={"plan_id": plan.name, "plan_name": plan.plan_name},
        message=_("Subscription plan updated")
    )


@frappe.whitelist()
@handle_exceptions
def activate_plan(plan_id):
    """Activate a subscription plan (Admin only)."""
    _require_admin()
    plan = frappe.get_doc("SaaS Subscription Plan", plan_id)
    plan.is_active = 1
    plan.save(ignore_permissions=True)
    frappe.db.commit()
    return ResponseFormatter.success(message=_("Plan activated"))


@frappe.whitelist()
@handle_exceptions
def deactivate_plan(plan_id):
    """Deactivate a subscription plan (Admin only)."""
    _require_admin()
    plan = frappe.get_doc("SaaS Subscription Plan", plan_id)
    plan.is_active = 0
    plan.save(ignore_permissions=True)
    frappe.db.commit()
    return ResponseFormatter.success(message=_("Plan deactivated"))


@frappe.whitelist()
@handle_exceptions
def get_plan_analytics():
    """Get subscription plan analytics (Admin only)."""
    _require_admin()

    plans = frappe.get_all(
        "SaaS Subscription Plan",
        fields=["name", "plan_name", "plan_code", "price", "billing_interval", "is_active"],
        order_by="sort_order asc"
    )

    analytics = []
    for plan in plans:
        active_subs = frappe.db.count("SaaS Subscriptions", {
            "plan_name": plan.name, "status": "Active"
        })
        trial_subs = frappe.db.count("SaaS Subscriptions", {
            "plan_name": plan.name, "status": "Trial"
        })
        total_revenue = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount_paid), 0) as revenue
            FROM `tabSaaS Subscriptions`
            WHERE plan_name = %s AND status IN ('Active', 'Expired')
        """, plan.name, as_dict=True)[0].revenue

        analytics.append({
            **plan,
            "active_subscribers": active_subs,
            "trial_subscribers": trial_subs,
            "total_revenue": float(total_revenue),
            "mrr": float(plan.price * active_subs) if plan.billing_interval == "Monthly" else 0
        })

    return ResponseFormatter.success(data=analytics, message=_("Plan analytics retrieved"))


@frappe.whitelist()
@handle_exceptions
def create_addon(addon_name, addon_type, price, unit, description=None):
    """Create an add-on product (Admin only)."""
    _require_admin()

    addon = frappe.get_doc({
        "doctype": "SaaS Subscription Plan",
        "plan_name": f"Add-on: {addon_name}",
        "plan_code": f"ADDON-{addon_name.upper().replace(' ', '-')}",
        "price": float(price),
        "billing_interval": "Monthly",
        "description": description or f"Add-on: {addon_name}",
        "is_active": 1,
        "max_companies": 0,
        "max_users": int(unit) if addon_type == "users" else 0,
        "max_storage_mb": int(unit) if addon_type == "storage" else 0,
    })
    addon.insert(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.created(
        data={"addon_id": addon.name},
        message=_("Add-on created")
    )


@frappe.whitelist()
@handle_exceptions
def list_addons():
    """List available add-ons."""
    addons = frappe.get_all(
        "SaaS Subscription Plan",
        filters={"plan_code": ["like", "ADDON-%"], "is_active": 1},
        fields=["name", "plan_name", "plan_code", "price", "description", "max_users", "max_storage_mb"]
    )
    return ResponseFormatter.success(data=addons, message=_("Add-ons retrieved"))


@frappe.whitelist(allow_guest=True)
def get_plan_details(plan_id):
    """Get public plan details with features."""
    plan = frappe.get_doc("SaaS Subscription Plan", plan_id)

    if not plan.is_active:
        return ResponseFormatter.not_found(_("Plan not found"))

    features = []
    for feat in plan.get("features", []):
        features.append({
            "feature_name": feat.feature_name,
            "description": feat.description,
            "is_included": feat.is_included,
            "limit_value": feat.limit_value
        })

    return ResponseFormatter.success(data={
        "plan_name": plan.plan_name,
        "plan_code": plan.plan_code,
        "price": plan.price,
        "currency": plan.currency,
        "setup_fee": plan.setup_fee,
        "billing_interval": plan.billing_interval,
        "description": plan.description,
        "max_companies": plan.max_companies,
        "max_users": plan.max_users,
        "max_storage_mb": plan.max_storage_mb,
        "allow_trial": plan.allow_trial,
        "trial_period_days": plan.trial_period_days,
        "features": features
    })


@frappe.whitelist(allow_guest=True)
def compare_plans():
    """Get all active plans for side-by-side comparison."""
    plans = frappe.get_all(
        "SaaS Subscription Plan",
        filters={"is_active": 1, "plan_code": ["not like", "ADDON-%"]},
        fields=[
            "name", "plan_name", "plan_code", "price", "currency", "setup_fee",
            "billing_interval", "description", "max_companies", "max_users",
            "max_storage_mb", "allow_trial", "trial_period_days"
        ],
        order_by="sort_order asc"
    )

    for plan in plans:
        plan["features"] = frappe.get_all(
            "SaaS Subscription Plan Features",
            filters={"parent": plan.name},
            fields=["feature_name", "description", "is_included", "limit_value"]
        )

    return ResponseFormatter.success(data=plans, message=_("Plans comparison"))
