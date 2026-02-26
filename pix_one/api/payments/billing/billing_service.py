"""
Module 4: Payments & Billing - Billing Management, Refunds, Payment Methods, Coupons
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime, add_days, getdate, today
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


# ==================== REFUNDS ====================

@frappe.whitelist()
@handle_exceptions
def request_refund(transaction_id, reason=None):
    """Request a refund for a completed payment."""
    user = frappe.session.user
    txn = frappe.get_doc("SaaS Payment Transaction", transaction_id)

    if txn.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your transaction"))

    if txn.status != "Completed":
        return ResponseFormatter.validation_error(_("Only completed transactions can be refunded"))

    # Check refund eligibility (within 30 days)
    if txn.payment_date and (now_datetime() - txn.payment_date).days > 30:
        return ResponseFormatter.validation_error(_("Refund window has expired (30 days)"))

    txn.status = "Refund Requested"
    txn.notes = (txn.notes or "") + f"\nRefund requested by {user}: {reason or 'No reason provided'}"
    txn.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "transaction_id": txn.name,
        "status": "Refund Requested",
        "amount": txn.amount,
        "message": _("Refund request submitted. It will be processed within 5-7 business days.")
    })


@frappe.whitelist()
@handle_exceptions
def get_refund_status(transaction_id):
    """Check refund status for a transaction."""
    user = frappe.session.user
    txn = frappe.get_doc("SaaS Payment Transaction", transaction_id)

    if txn.customer_id != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Not your transaction"))

    return ResponseFormatter.success(data={
        "transaction_id": txn.name,
        "status": txn.status,
        "amount": txn.amount,
        "refund_amount": txn.get("refund_amount") or 0,
        "refund_date": txn.get("refund_date"),
    })


# ==================== PAYMENT METHODS ====================

@frappe.whitelist()
@handle_exceptions
def add_payment_method(method_type, token, label=None, is_default=0):
    """Save a payment method (card token from gateway)."""
    user = frappe.session.user

    method = frappe.get_doc({
        "doctype": "SaaS Payment Method",
        "user": user,
        "method_type": method_type,
        "gateway_token": token,
        "label": label or f"{method_type} ending in ****",
        "is_default": int(is_default)
    })
    method.insert(ignore_permissions=True)

    if int(is_default):
        frappe.db.sql("""
            UPDATE `tabSaaS Payment Method`
            SET is_default = 0
            WHERE user = %s AND name != %s
        """, (user, method.name))

    frappe.db.commit()

    return ResponseFormatter.created(data={"method_id": method.name})


@frappe.whitelist()
@handle_exceptions
def get_payment_methods():
    """List saved payment methods for the current user."""
    user = frappe.session.user
    methods = frappe.get_all(
        "SaaS Payment Method",
        filters={"user": user},
        fields=["name", "method_type", "label", "is_default", "creation"],
        order_by="is_default desc, creation desc"
    )
    return ResponseFormatter.success(data=methods)


@frappe.whitelist()
@handle_exceptions
def remove_payment_method(method_id):
    """Remove a saved payment method."""
    user = frappe.session.user
    method = frappe.get_doc("SaaS Payment Method", method_id)

    if method.user != user:
        return ResponseFormatter.forbidden(_("Not your payment method"))

    frappe.delete_doc("SaaS Payment Method", method_id, ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.deleted(_("Payment method removed"))


@frappe.whitelist()
@handle_exceptions
def set_default_method(method_id):
    """Set a payment method as default."""
    user = frappe.session.user
    method = frappe.get_doc("SaaS Payment Method", method_id)

    if method.user != user:
        return ResponseFormatter.forbidden(_("Not your payment method"))

    frappe.db.sql("""
        UPDATE `tabSaaS Payment Method` SET is_default = 0 WHERE user = %s
    """, user)
    frappe.db.set_value("SaaS Payment Method", method_id, "is_default", 1)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Default payment method updated"))


# ==================== BILLING ====================

@frappe.whitelist()
@handle_exceptions
def get_billing_history(page=1, limit=20):
    """Get complete billing history for the current user."""
    user = frappe.session.user
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    transactions = frappe.get_all(
        "SaaS Payment Transaction",
        filters={"customer_id": user},
        fields=[
            "name", "transaction_id", "amount", "currency", "status",
            "transaction_type", "payment_method", "payment_gateway",
            "payment_date", "subscription_id", "creation"
        ],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS Payment Transaction", {"customer_id": user})

    return ResponseFormatter.paginated(data=transactions, total=total, page=page, limit=limit)


@frappe.whitelist()
@handle_exceptions
def get_upcoming_invoice(subscription_id):
    """Preview the next invoice for a subscription."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    return ResponseFormatter.success(data={
        "subscription_id": sub.name,
        "plan": plan.plan_name,
        "amount": plan.price,
        "currency": plan.currency or "USD",
        "billing_date": str(sub.end_date) if sub.end_date else None,
        "auto_renew": sub.auto_renew,
    })


@frappe.whitelist()
@handle_exceptions
def apply_coupon(subscription_id, coupon_code):
    """Apply a discount coupon to a subscription."""
    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)

    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Not your subscription"))

    if not frappe.db.exists("SaaS Coupon Code", {"code": coupon_code, "is_active": 1}):
        return ResponseFormatter.validation_error(_("Invalid or expired coupon code"))

    coupon = frappe.get_doc("SaaS Coupon Code", {"code": coupon_code})

    if coupon.max_uses and coupon.times_used >= coupon.max_uses:
        return ResponseFormatter.validation_error(_("Coupon has reached its usage limit"))

    if coupon.valid_until and getdate(coupon.valid_until) < getdate(today()):
        return ResponseFormatter.validation_error(_("Coupon has expired"))

    # Apply discount
    discount_amount = 0
    if coupon.discount_type == "Percentage":
        discount_amount = flt(sub.price * coupon.discount_value / 100, 2)
    else:
        discount_amount = flt(coupon.discount_value, 2)

    coupon.times_used = (coupon.times_used or 0) + 1
    coupon.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "coupon_code": coupon_code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount_amount,
        "final_amount": max(0, flt(sub.price - discount_amount, 2))
    })


@frappe.whitelist()
@handle_exceptions
def update_billing_address(
    address_line1, city, country, state=None, postal_code=None, address_line2=None
):
    """Update billing address for the current user."""
    user = frappe.session.user

    # Update or create billing address
    existing = frappe.db.get_value("Address", {
        "email_id": user, "address_type": "Billing"
    }, "name")

    if existing:
        address = frappe.get_doc("Address", existing)
    else:
        address = frappe.new_doc("Address")
        address.address_type = "Billing"
        address.email_id = user

    address.address_line1 = address_line1
    address.address_line2 = address_line2
    address.city = city
    address.state = state
    address.pincode = postal_code
    address.country = country
    address.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(
        data={"address_id": address.name},
        message=_("Billing address updated")
    )
