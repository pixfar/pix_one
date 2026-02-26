"""
Module 12: Support & Helpdesk - Tickets, Knowledge Base, System Status
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


# ==================== SUPPORT TICKETS ====================

@frappe.whitelist()
@handle_exceptions
def create_ticket(subject, description, priority="Medium", category=None):
    """Create a new support ticket."""
    user = frappe.session.user

    if not subject or not description:
        return ResponseFormatter.validation_error(_("Subject and description are required"))

    ticket = frappe.get_doc({
        "doctype": "SaaS Support Ticket",
        "subject": subject,
        "description": description,
        "priority": priority,
        "category": category,
        "raised_by": user,
        "status": "Open"
    })
    ticket.insert(ignore_permissions=True)
    frappe.db.commit()

    # Notify admin
    try:
        admins = frappe.get_all("Has Role", {"role": "System Manager"}, pluck="parent", limit=5)
        for admin in admins:
            frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": admin,
                "from_user": user,
                "subject": _("New support ticket: {0}").format(subject),
                "email_content": description[:200],
                "document_type": "SaaS Support Ticket",
                "document_name": ticket.name,
                "type": "Alert",
                "read": 0
            }).insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass

    return ResponseFormatter.created(data={
        "ticket_id": ticket.name,
        "status": "Open"
    }, message=_("Support ticket created. We'll respond within 24 hours."))


@frappe.whitelist()
@handle_exceptions
def list_tickets(page=1, limit=20, status=None):
    """List support tickets for the current user."""
    user = frappe.session.user
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {"raised_by": user}

    # Admins can see all tickets
    if "System Manager" in frappe.get_roles(user):
        filters = {}

    if status:
        filters["status"] = status

    tickets = frappe.get_all(
        "SaaS Support Ticket",
        filters=filters,
        fields=[
            "name", "subject", "status", "priority", "category",
            "raised_by", "assigned_to", "creation", "modified"
        ],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS Support Ticket", filters)

    return ResponseFormatter.paginated(data=tickets, total=total, page=page, limit=limit)


@frappe.whitelist()
@handle_exceptions
def get_ticket(ticket_id):
    """Get ticket details with all replies."""
    user = frappe.session.user
    ticket = frappe.get_doc("SaaS Support Ticket", ticket_id)

    if ticket.raised_by != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    replies = frappe.get_all(
        "SaaS Support Reply",
        filters={"parent": ticket_id, "parenttype": "SaaS Support Ticket"},
        fields=["name", "reply_by", "reply_text", "is_staff_reply", "creation"],
        order_by="creation asc"
    )

    return ResponseFormatter.success(data={
        "ticket_id": ticket.name,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "category": ticket.category,
        "raised_by": ticket.raised_by,
        "assigned_to": ticket.assigned_to,
        "created_at": ticket.creation,
        "updated_at": ticket.modified,
        "replies": replies
    })


@frappe.whitelist()
@handle_exceptions
def reply_ticket(ticket_id, message):
    """Reply to a support ticket."""
    user = frappe.session.user

    if not message:
        return ResponseFormatter.validation_error(_("Message is required"))

    ticket = frappe.get_doc("SaaS Support Ticket", ticket_id)

    if ticket.raised_by != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    is_staff = "System Manager" in frappe.get_roles(user)

    ticket.append("replies", {
        "reply_by": user,
        "reply_text": message,
        "is_staff_reply": 1 if is_staff else 0
    })

    # Update status
    if is_staff and ticket.status == "Open":
        ticket.status = "Replied"
    elif not is_staff and ticket.status in ("Replied", "Closed"):
        ticket.status = "Reopened"

    ticket.save(ignore_permissions=True)
    frappe.db.commit()

    # Notify the other party
    notify_user = ticket.raised_by if is_staff else (ticket.assigned_to or "")
    if notify_user:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "for_user": notify_user,
                "from_user": user,
                "subject": _("New reply on ticket: {0}").format(ticket.subject),
                "email_content": message[:200],
                "document_type": "SaaS Support Ticket",
                "document_name": ticket_id,
                "type": "Alert",
                "read": 0
            }).insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            pass

    return ResponseFormatter.success(message=_("Reply sent"))


@frappe.whitelist()
@handle_exceptions
def close_ticket(ticket_id, resolution=None):
    """Close a support ticket."""
    user = frappe.session.user
    ticket = frappe.get_doc("SaaS Support Ticket", ticket_id)

    if ticket.raised_by != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    ticket.status = "Closed"
    if resolution:
        ticket.resolution = resolution
    ticket.closed_at = now_datetime()
    ticket.save(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Ticket closed"))


@frappe.whitelist()
@handle_exceptions
def reopen_ticket(ticket_id, reason=None):
    """Reopen a closed ticket."""
    user = frappe.session.user
    ticket = frappe.get_doc("SaaS Support Ticket", ticket_id)

    if ticket.raised_by != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    if ticket.status != "Closed":
        return ResponseFormatter.validation_error(_("Only closed tickets can be reopened"))

    ticket.status = "Reopened"
    ticket.save(ignore_permissions=True)

    if reason:
        ticket.append("replies", {
            "reply_by": user,
            "reply_text": f"Ticket reopened: {reason}",
            "is_staff_reply": 0
        })
        ticket.save(ignore_permissions=True)

    frappe.db.commit()

    return ResponseFormatter.success(message=_("Ticket reopened"))


@frappe.whitelist()
@handle_exceptions
def upload_attachment(ticket_id, file_url):
    """Attach a file to a support ticket."""
    user = frappe.session.user
    ticket = frappe.get_doc("SaaS Support Ticket", ticket_id)

    if ticket.raised_by != user and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    # Frappe's file attachment mechanism
    frappe.get_doc({
        "doctype": "File",
        "file_url": file_url,
        "attached_to_doctype": "SaaS Support Ticket",
        "attached_to_name": ticket_id,
    }).insert(ignore_permissions=True)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("File attached"))


# ==================== KNOWLEDGE BASE ====================

@frappe.whitelist(allow_guest=True)
def search_kb(query, category=None, page=1, limit=10):
    """Search the knowledge base."""
    page = int(page)
    limit = min(int(limit), 50)
    offset = (page - 1) * limit

    filters = {"is_published": 1}
    if category:
        filters["category"] = category

    articles = frappe.get_all(
        "SaaS KB Article",
        filters=filters,
        or_filters=[
            ["title", "like", f"%{query}%"],
            ["content", "like", f"%{query}%"],
            ["tags", "like", f"%{query}%"]
        ] if query else None,
        fields=["name", "title", "category", "summary", "view_count", "creation"],
        order_by="view_count desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS KB Article", filters)

    return ResponseFormatter.paginated(data=articles, total=total, page=page, limit=limit)


@frappe.whitelist(allow_guest=True)
def get_article(article_id):
    """Get a knowledge base article and increment view count."""
    if not frappe.db.exists("SaaS KB Article", article_id):
        return ResponseFormatter.not_found(_("Article not found"))

    article = frappe.get_doc("SaaS KB Article", article_id)

    if not article.is_published:
        return ResponseFormatter.not_found(_("Article not found"))

    # Increment view count
    frappe.db.sql("""
        UPDATE `tabSaaS KB Article`
        SET view_count = COALESCE(view_count, 0) + 1
        WHERE name = %s
    """, article_id)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "title": article.title,
        "content": article.content,
        "category": article.category,
        "tags": article.tags,
        "summary": article.summary,
        "view_count": (article.view_count or 0) + 1,
        "created_at": article.creation,
        "updated_at": article.modified
    })


# ==================== SYSTEM STATUS ====================

@frappe.whitelist(allow_guest=True)
def get_system_status():
    """Get platform status page data (public)."""
    components = []

    # Database status
    try:
        frappe.db.sql("SELECT 1")
        components.append({"name": "Database", "status": "operational"})
    except Exception:
        components.append({"name": "Database", "status": "outage"})

    # Cache status
    try:
        frappe.cache().set_value("status_check", "ok", expires_in_sec=5)
        components.append({"name": "Cache", "status": "operational"})
    except Exception:
        components.append({"name": "Cache", "status": "outage"})

    # API status
    components.append({"name": "API", "status": "operational"})

    # Payment gateway
    components.append({"name": "Payment Processing", "status": "operational"})

    overall = "operational" if all(c["status"] == "operational" for c in components) else "degraded"

    return ResponseFormatter.success(data={
        "overall_status": overall,
        "components": components,
        "last_updated": str(now_datetime())
    })
