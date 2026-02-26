"""
Module 1: Authentication & Identity - Security Endpoints
"""

import frappe
from frappe import _
from frappe.utils.password import update_password as frappe_update_password
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


@frappe.whitelist()
@handle_exceptions
def enable_2fa():
    """Enable two-factor authentication for the current user."""
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    if frappe.db.get_single_value("System Settings", "enable_two_factor_auth"):
        # System-wide 2FA - just toggle user-level
        pass

    # Generate TOTP secret or enable OTP-based 2FA
    frappe.db.set_value("User", user, "two_factor_is_enabled", 1)
    frappe.db.commit()

    return ResponseFormatter.success(
        data={"two_factor_enabled": True},
        message=_("Two-factor authentication enabled")
    )


@frappe.whitelist()
@handle_exceptions
def disable_2fa(password):
    """Disable two-factor authentication (requires password confirmation)."""
    user = frappe.session.user

    if not password:
        return ResponseFormatter.validation_error(_("Password is required to disable 2FA"))

    # Verify password
    from frappe.core.doctype.user.user import User
    user_info = User.find_by_credentials(user, password, validate_password=True)
    if not user_info or not user_info.get("is_authenticated"):
        return ResponseFormatter.unauthorized(_("Invalid password"))

    frappe.db.set_value("User", user, "two_factor_is_enabled", 0)
    frappe.db.commit()

    return ResponseFormatter.success(
        data={"two_factor_enabled": False},
        message=_("Two-factor authentication disabled")
    )


@frappe.whitelist()
@handle_exceptions
def change_password(current_password, new_password):
    """Change the current user's password."""
    user = frappe.session.user

    if not current_password or not new_password:
        return ResponseFormatter.validation_error(_("Current and new passwords are required"))

    if len(new_password) < 8:
        return ResponseFormatter.validation_error(_("New password must be at least 8 characters"))

    # Verify current password
    from frappe.core.doctype.user.user import User
    user_info = User.find_by_credentials(user, current_password, validate_password=True)
    if not user_info or not user_info.get("is_authenticated"):
        return ResponseFormatter.unauthorized(_("Current password is incorrect"))

    # Update password
    frappe_update_password(user, new_password)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Password changed successfully"))


@frappe.whitelist()
@handle_exceptions
def get_security_log(page=1, limit=20):
    """Get the security/audit log for the current user."""
    user = frappe.session.user
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    logs = frappe.get_all(
        "Activity Log",
        filters={"user": user},
        fields=["name", "subject", "operation", "status", "creation", "ip_address"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("Activity Log", {"user": user})

    return ResponseFormatter.paginated(
        data=logs,
        total=total,
        page=page,
        limit=limit,
        message=_("Security log retrieved")
    )
