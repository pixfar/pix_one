"""
Module 1: Authentication & Identity - Registration Endpoints
"""

import frappe
from frappe import _
from frappe.utils import random_string, cint
from pix_one.utils.jwt_auth import generate_access_token, generate_refresh_token
from pix_one.utils.error_handler import throw_error, ErrorCode, success_response
from pix_one.utils.rate_limit import rate_limit_guest


@frappe.whitelist(allow_guest=True)
def register(email, full_name, password, mobile_no=None):
    """Register a new user account with email verification via OTP."""
    rate_limit_guest(f"register:{email}", limit=5, seconds=3600)

    if not email or not full_name or not password:
        throw_error(ErrorCode.MISSING_REQUIRED_FIELD, _("Email, full name, and password are required"))

    email = email.strip().lower()

    if frappe.db.exists("User", email):
        throw_error(ErrorCode.DUPLICATE_ENTRY, _("An account with this email already exists"))

    if len(password) < 8:
        throw_error(ErrorCode.INVALID_INPUT, _("Password must be at least 8 characters"))

    # Generate OTP
    otp = random_string(6, digits=True)
    first_name = full_name.split(" ")[0]
    last_name = " ".join(full_name.split(" ")[1:]) if len(full_name.split(" ")) > 1 else ""

    # Cache registration data
    cache_key = f"registration:{email}"
    frappe.cache().set_value(cache_key, {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "mobile_no": mobile_no,
        "otp": otp
    }, expires_in_sec=600)

    # Send verification email
    try:
        frappe.sendmail(
            recipients=[email],
            subject=_("Verify your email - PixOne"),
            message=_("Your verification code is: <strong>{0}</strong>. It expires in 10 minutes.").format(otp),
            now=True
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Registration Email Error")

    return success_response(
        message=_("Verification code sent to your email"),
        data={"email": email, "requires_verification": True}
    )


@frappe.whitelist(allow_guest=True)
def verify_email(email, otp):
    """Verify email with OTP and create the user account."""
    rate_limit_guest(f"verify_email:{email}", limit=10, seconds=600)

    if not email or not otp:
        throw_error(ErrorCode.MISSING_REQUIRED_FIELD, _("Email and OTP are required"))

    cache_key = f"registration:{email}"
    cached_data = frappe.cache().get_value(cache_key)

    if not cached_data:
        throw_error(ErrorCode.TOKEN_EXPIRED, _("Registration session expired. Please register again."))

    if cached_data.get("otp") != otp.strip():
        throw_error(ErrorCode.INVALID_CREDENTIALS, _("Invalid verification code"))

    # Create user
    try:
        user = frappe.get_doc({
            "doctype": "User",
            "email": cached_data["email"],
            "first_name": cached_data["first_name"],
            "last_name": cached_data["last_name"],
            "mobile_no": cached_data.get("mobile_no"),
            "enabled": 1,
            "user_type": "Website User",
            "new_password": cached_data["password"],
            "send_welcome_email": 0
        })
        user.insert(ignore_permissions=True)
        frappe.db.commit()

        # Clear cache
        frappe.cache().delete_value(cache_key)

        # Auto-login
        from pix_one.shared.arcpos_settings.system_settings import default_system_settings
        access_token = generate_access_token(
            cached_data["email"],
            expires_in_hours=int(default_system_settings().access_token_expiry or 24)
        )
        refresh_token = generate_refresh_token(
            cached_data["email"],
            expires_in_days=int(default_system_settings().refresh_token_expiry or 30)
        )

        return success_response(
            message=_("Account created successfully"),
            data={
                "user": {
                    "email": user.email,
                    "full_name": user.full_name,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer"
            }
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "User Registration Error")
        throw_error(ErrorCode.OPERATION_FAILED, _("Failed to create account: {0}").format(str(e)))


@frappe.whitelist(allow_guest=True)
def resend_verification(email):
    """Resend verification OTP for pending registration."""
    rate_limit_guest(f"resend_verify:{email}", limit=3, seconds=600)

    cache_key = f"registration:{email}"
    cached_data = frappe.cache().get_value(cache_key)

    if not cached_data:
        throw_error(ErrorCode.RESOURCE_NOT_FOUND, _("No pending registration found for this email"))

    # Generate new OTP
    otp = random_string(6, digits=True)
    cached_data["otp"] = otp
    frappe.cache().set_value(cache_key, cached_data, expires_in_sec=600)

    try:
        frappe.sendmail(
            recipients=[email],
            subject=_("Verify your email - PixOne"),
            message=_("Your new verification code is: <strong>{0}</strong>. It expires in 10 minutes.").format(otp),
            now=True
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Resend Verification Email Error")

    return success_response(message=_("Verification code resent to your email"))
