"""
Module 1: Authentication & Identity - Session Management Endpoints
"""

import frappe
from frappe import _
from pix_one.utils.jwt_auth import (
    get_active_sessions_key, revoke_specific_sessions, remove_user_session
)
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


@frappe.whitelist()
@handle_exceptions
def get_active_sessions():
    """List all active sessions for the current user."""
    user = frappe.session.user
    cache_key = get_active_sessions_key(user)
    active_sessions = frappe.cache().get_value(cache_key) or []

    sessions = []
    for i, session_iat in enumerate(active_sessions):
        from datetime import datetime
        created_at = datetime.utcfromtimestamp(session_iat).isoformat() if session_iat else None
        sessions.append({
            "session_id": str(session_iat),
            "created_at": created_at,
            "is_current": i == len(active_sessions) - 1
        })

    return ResponseFormatter.success(
        data={"sessions": sessions, "total": len(sessions)},
        message=_("Active sessions retrieved")
    )


@frappe.whitelist()
@handle_exceptions
def revoke_session(session_id):
    """Revoke a specific session by its identifier."""
    user = frappe.session.user

    if not session_id:
        return ResponseFormatter.validation_error(_("Session ID is required"))

    try:
        session_iat = int(session_id)
    except (ValueError, TypeError):
        return ResponseFormatter.validation_error(_("Invalid session ID"))

    # Remove from active sessions
    remove_user_session(user, session_iat)

    # Add to revoked list
    revoke_specific_sessions(user, [session_iat])

    return ResponseFormatter.success(message=_("Session revoked successfully"))
