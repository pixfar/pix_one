"""
Module 11: User & Team Management - Team Members, Invitations, Roles
"""

import frappe
from frappe import _
from frappe.utils import random_string, now_datetime, add_days, today, getdate
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


def _get_user_subscription():
    """Get the current user's active subscription."""
    user = frappe.session.user
    sub_id = frappe.db.get_value("SaaS Subscriptions", {
        "customer_id": user, "status": "Active"
    }, "name")
    if not sub_id:
        frappe.throw(_("No active subscription"), frappe.ValidationError)
    return sub_id


def _check_user_limit(subscription_id):
    """Check if the user limit has been reached."""
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    plan = frappe.get_doc("SaaS Subscription Plan", sub.plan_name)

    current_members = frappe.db.count("SaaS Team Member", {
        "subscription_id": subscription_id, "status": ["in", ["Active", "Invited"]]
    })

    max_users = plan.max_users or 5
    if current_members >= max_users:
        frappe.throw(
            _("User limit reached ({0}/{1}). Please upgrade your plan.").format(current_members, max_users),
            frappe.ValidationError
        )


@frappe.whitelist()
@handle_exceptions
def list_members(subscription_id=None):
    """List all team members for the subscription."""
    if not subscription_id:
        subscription_id = _get_user_subscription()

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != frappe.session.user and "System Manager" not in frappe.get_roles(frappe.session.user):
        return ResponseFormatter.forbidden(_("Access denied"))

    members = frappe.get_all(
        "SaaS Team Member",
        filters={"subscription_id": subscription_id},
        fields=["name", "user_email", "role", "status", "invited_by", "joined_at", "creation"],
        order_by="creation asc"
    )

    # Add owner
    owner_data = {
        "user_email": sub.customer_id,
        "role": "Owner",
        "status": "Active",
        "is_owner": True
    }

    return ResponseFormatter.success(data={
        "owner": owner_data,
        "members": members,
        "total": len(members) + 1
    })


@frappe.whitelist()
@handle_exceptions
def invite_member(email, role="Member", subscription_id=None):
    """Invite a user to the team."""
    if not subscription_id:
        subscription_id = _get_user_subscription()

    user = frappe.session.user
    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != user:
        return ResponseFormatter.forbidden(_("Only the subscription owner can invite members"))

    # Check if already a member
    existing = frappe.db.exists("SaaS Team Member", {
        "subscription_id": subscription_id,
        "user_email": email,
        "status": ["in", ["Active", "Invited"]]
    })
    if existing:
        return ResponseFormatter.validation_error(_("User is already a team member"))

    # Check user limit
    _check_user_limit(subscription_id)

    # Generate invite token
    invite_token = random_string(32)

    member = frappe.get_doc({
        "doctype": "SaaS Team Member",
        "subscription_id": subscription_id,
        "user_email": email,
        "role": role,
        "status": "Invited",
        "invited_by": user,
        "invite_token": invite_token,
        "invite_expires_at": add_days(today(), 7)
    })
    member.insert(ignore_permissions=True)
    frappe.db.commit()

    # Send invite email
    invite_url = f"{frappe.utils.get_url()}/pixone/accept-invite?token={invite_token}"
    try:
        frappe.sendmail(
            recipients=[email],
            subject=_("You've been invited to join {0} on PixOne").format(sub.customer_id),
            message=_(
                "You have been invited to join a team on PixOne.<br><br>"
                "Role: {0}<br>"
                "Invited by: {1}<br><br>"
                "<a href='{2}'>Accept Invitation</a><br><br>"
                "This invitation expires in 7 days."
            ).format(role, user, invite_url),
            now=True
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Team Invite Email Error")

    return ResponseFormatter.created(data={
        "member_id": member.name,
        "email": email,
        "role": role,
        "status": "Invited"
    }, message=_("Invitation sent to {0}").format(email))


@frappe.whitelist()
@handle_exceptions
def remove_member(member_id):
    """Remove a team member."""
    member = frappe.get_doc("SaaS Team Member", member_id)
    sub = frappe.get_doc("SaaS Subscriptions", member.subscription_id)

    if sub.customer_id != frappe.session.user:
        return ResponseFormatter.forbidden(_("Only the owner can remove members"))

    member.status = "Removed"
    member.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Team member removed"))


@frappe.whitelist()
@handle_exceptions
def update_role(member_id, new_role):
    """Change a team member's role."""
    member = frappe.get_doc("SaaS Team Member", member_id)
    sub = frappe.get_doc("SaaS Subscriptions", member.subscription_id)

    if sub.customer_id != frappe.session.user:
        return ResponseFormatter.forbidden(_("Only the owner can change roles"))

    member.role = new_role
    member.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Role updated to {0}").format(new_role))


@frappe.whitelist()
@handle_exceptions
def get_pending_invites(subscription_id=None):
    """List pending invitations."""
    if not subscription_id:
        subscription_id = _get_user_subscription()

    invites = frappe.get_all(
        "SaaS Team Member",
        filters={"subscription_id": subscription_id, "status": "Invited"},
        fields=["name", "user_email", "role", "invited_by", "creation", "invite_expires_at"]
    )

    return ResponseFormatter.success(data=invites)


@frappe.whitelist()
@handle_exceptions
def resend_invite(member_id):
    """Resend an invitation email."""
    member = frappe.get_doc("SaaS Team Member", member_id)
    sub = frappe.get_doc("SaaS Subscriptions", member.subscription_id)

    if sub.customer_id != frappe.session.user:
        return ResponseFormatter.forbidden(_("Only the owner can resend invites"))

    if member.status != "Invited":
        return ResponseFormatter.validation_error(_("This invitation is no longer pending"))

    # Regenerate token and extend expiry
    member.invite_token = random_string(32)
    member.invite_expires_at = add_days(today(), 7)
    member.save(ignore_permissions=True)
    frappe.db.commit()

    invite_url = f"{frappe.utils.get_url()}/pixone/accept-invite?token={member.invite_token}"
    try:
        frappe.sendmail(
            recipients=[member.user_email],
            subject=_("Reminder: You've been invited to PixOne"),
            message=_("Invitation reminder.<br><a href='{0}'>Accept Invitation</a>").format(invite_url),
            now=True
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Resend Invite Error")

    return ResponseFormatter.success(message=_("Invitation resent"))


@frappe.whitelist()
@handle_exceptions
def cancel_invite(member_id):
    """Cancel a pending invitation."""
    member = frappe.get_doc("SaaS Team Member", member_id)
    sub = frappe.get_doc("SaaS Subscriptions", member.subscription_id)

    if sub.customer_id != frappe.session.user:
        return ResponseFormatter.forbidden(_("Only the owner can cancel invites"))

    if member.status != "Invited":
        return ResponseFormatter.validation_error(_("This invitation is no longer pending"))

    frappe.delete_doc("SaaS Team Member", member_id, ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.deleted(_("Invitation cancelled"))


# ==================== ROLES & ACTIVITY ====================

@frappe.whitelist()
@handle_exceptions
def list_roles():
    """List available roles for team members."""
    roles = [
        {"name": "Owner", "description": "Full access. Can manage subscription, billing, and team.", "assignable": False},
        {"name": "Admin", "description": "Can manage team members and companies.", "assignable": True},
        {"name": "Member", "description": "Can access companies and apps.", "assignable": True},
        {"name": "Viewer", "description": "Read-only access to companies.", "assignable": True},
    ]
    return ResponseFormatter.success(data=roles)


@frappe.whitelist()
@handle_exceptions
def get_activity_log(subscription_id=None, page=1, limit=20):
    """Get team activity log."""
    if not subscription_id:
        subscription_id = _get_user_subscription()

    sub = frappe.get_doc("SaaS Subscriptions", subscription_id)
    if sub.customer_id != frappe.session.user and "System Manager" not in frappe.get_roles(frappe.session.user):
        return ResponseFormatter.forbidden(_("Access denied"))

    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    logs = frappe.get_all(
        "SaaS Audit Log",
        filters={"reference_doctype": "SaaS Subscriptions", "reference_name": subscription_id},
        fields=["name", "action", "user", "data", "creation"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS Audit Log", {
        "reference_doctype": "SaaS Subscriptions", "reference_name": subscription_id
    })

    return ResponseFormatter.paginated(data=logs, total=total, page=page, limit=limit)
