"""
Module 10: Notifications - User Notifications, Preferences, Push Subscriptions
"""

import frappe
from frappe import _
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


@frappe.whitelist()
@handle_exceptions
def list_notifications(page=1, limit=20, read_status=None):
    """List notifications for the current user."""
    user = frappe.session.user
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {"for_user": user}
    if read_status == "unread":
        filters["read"] = 0
    elif read_status == "read":
        filters["read"] = 1

    notifications = frappe.get_all(
        "Notification Log",
        filters=filters,
        fields=[
            "name", "subject", "email_content", "document_type", "document_name",
            "type", "read", "from_user", "creation"
        ],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("Notification Log", filters)
    unread = frappe.db.count("Notification Log", {"for_user": user, "read": 0})

    return ResponseFormatter.paginated(
        data=notifications,
        total=total,
        page=page,
        limit=limit,
        message=_("{0} unread notifications").format(unread)
    )


@frappe.whitelist()
@handle_exceptions
def mark_read(notification_id):
    """Mark a notification as read."""
    user = frappe.session.user
    notif = frappe.get_doc("Notification Log", notification_id)

    if notif.for_user != user:
        return ResponseFormatter.forbidden(_("Not your notification"))

    notif.db_set("read", 1)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Notification marked as read"))


@frappe.whitelist()
@handle_exceptions
def mark_all_read():
    """Mark all notifications as read for the current user."""
    user = frappe.session.user

    frappe.db.sql("""
        UPDATE `tabNotification Log` SET `read` = 1
        WHERE for_user = %s AND `read` = 0
    """, user)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("All notifications marked as read"))


@frappe.whitelist()
@handle_exceptions
def get_preferences():
    """Get notification preferences for the current user."""
    user = frappe.session.user

    # Get from cache or default
    cache_key = f"notification_prefs:{user}"
    prefs = frappe.cache().get_value(cache_key) or {
        "email_enabled": True,
        "push_enabled": True,
        "subscription_alerts": True,
        "billing_alerts": True,
        "system_alerts": True,
        "marketing_emails": False,
        "weekly_digest": True
    }

    return ResponseFormatter.success(data=prefs)


@frappe.whitelist()
@handle_exceptions
def update_preferences(**kwargs):
    """Update notification preferences."""
    user = frappe.session.user

    allowed_fields = [
        "email_enabled", "push_enabled", "subscription_alerts",
        "billing_alerts", "system_alerts", "marketing_emails", "weekly_digest"
    ]

    cache_key = f"notification_prefs:{user}"
    prefs = frappe.cache().get_value(cache_key) or {}

    for field in allowed_fields:
        if field in kwargs:
            prefs[field] = bool(int(kwargs[field])) if kwargs[field] is not None else prefs.get(field, True)

    frappe.cache().set_value(cache_key, prefs, expires_in_sec=365 * 24 * 3600)

    return ResponseFormatter.success(data=prefs, message=_("Preferences updated"))


@frappe.whitelist()
@handle_exceptions
def subscribe_push(token, device_type="web", device_name=None):
    """Register a push notification token."""
    user = frappe.session.user

    if not token:
        return ResponseFormatter.validation_error(_("Token is required"))

    # Check if token already exists
    existing = frappe.db.exists("SaaS Push Token", {"user": user, "token": token})
    if existing:
        return ResponseFormatter.success(message=_("Token already registered"))

    frappe.get_doc({
        "doctype": "SaaS Push Token",
        "user": user,
        "token": token,
        "device_type": device_type,
        "device_name": device_name or device_type,
        "is_active": 1
    }).insert(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.created(message=_("Push notification token registered"))


@frappe.whitelist()
@handle_exceptions
def unsubscribe_push(token):
    """Unregister a push notification token."""
    user = frappe.session.user

    existing = frappe.db.exists("SaaS Push Token", {"user": user, "token": token})
    if existing:
        frappe.delete_doc("SaaS Push Token", existing, ignore_permissions=True)
        frappe.db.commit()

    return ResponseFormatter.success(message=_("Push notification token removed"))


# ==================== ADMIN BULK NOTIFICATIONS ====================

@frappe.whitelist()
@handle_exceptions
def send_bulk(recipients, subject, message, notification_type="Alert"):
    """Send bulk notification to multiple users (Admin only)."""
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        return ResponseFormatter.forbidden(_("Admin access required"))

    import json
    if isinstance(recipients, str):
        recipients = json.loads(recipients)

    sent_count = 0
    for user_email in recipients:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": user_email,
                "from_user": frappe.session.user,
                "subject": subject,
                "email_content": message,
                "type": notification_type,
                "read": 0
            }).insert(ignore_permissions=True)
            sent_count += 1
        except Exception:
            pass

    frappe.db.commit()

    return ResponseFormatter.success(data={
        "sent": sent_count,
        "total": len(recipients)
    }, message=_("{0} notifications sent").format(sent_count))
