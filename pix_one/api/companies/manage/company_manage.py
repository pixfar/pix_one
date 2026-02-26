"""
Module 5: Company/Business Management - Extended Management Endpoints
"""

import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any

import frappe
from frappe import _
from frappe.utils import now_datetime
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions

BENCH_PATH = os.getenv("BENCH_PATH", "/workspace/development/frappe-bench")


def _run(cmd: str):
    res = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=300)
    return res.returncode, res.stdout, res.stderr


def _run_bench(cmd_list):
    if not os.path.isdir(BENCH_PATH):
        return 1, "", f"Bench path not found: {BENCH_PATH}"
    shell_cmd = f"cd {shlex.quote(BENCH_PATH)} && {shlex.join(cmd_list)}"
    return _run(shell_cmd)


def _check_permission(company_doc):
    user = frappe.session.user
    if user != company_doc.customer_id and "System Manager" not in frappe.get_roles(user):
        frappe.throw(_("Access denied"), frappe.PermissionError)


@frappe.whitelist()
@handle_exceptions
def get_company_details(company_id):
    """Get full company details with status and metrics."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    return ResponseFormatter.success(data={
        "company_id": doc.name,
        "company_name": doc.company_name,
        "company_abbr": doc.company_abbr,
        "status": doc.status,
        "site_name": doc.site_name,
        "site_url": doc.site_url,
        "domain": doc.domain,
        "subscription_id": doc.subscription_id,
        "admin_email": doc.admin_email,
        "default_currency": doc.default_currency,
        "country": doc.country,
        "current_users": doc.current_users or 0,
        "current_storage_mb": doc.current_storage_mb or 0,
        "provisioning_started_at": doc.provisioning_started_at,
        "provisioning_completed_at": doc.provisioning_completed_at,
        "creation": doc.creation,
    })


@frappe.whitelist()
@handle_exceptions
def suspend_company(company_id, reason=None):
    """Suspend a company/site."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if doc.status == "Suspended":
        return ResponseFormatter.validation_error(_("Company is already suspended"))

    doc.db_set("status", "Suspended", update_modified=True)
    doc.add_comment("Comment", f"Company suspended. Reason: {reason or 'No reason provided'}")
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Company suspended"))


@frappe.whitelist()
@handle_exceptions
def reactivate_company(company_id):
    """Reactivate a suspended company."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if doc.status != "Suspended":
        return ResponseFormatter.validation_error(_("Company is not suspended"))

    # Verify subscription is still active
    if doc.subscription_id:
        sub_status = frappe.db.get_value("SaaS Subscriptions", doc.subscription_id, "status")
        if sub_status != "Active":
            return ResponseFormatter.validation_error(
                _("Cannot reactivate: subscription is {0}").format(sub_status)
            )

    doc.db_set("status", "Active", update_modified=True)
    doc.add_comment("Comment", "Company reactivated")
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Company reactivated"))


@frappe.whitelist()
@handle_exceptions
def get_provisioning_status(company_id):
    """Get real-time provisioning progress."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    # Check Redis for real-time progress
    progress_key = f"saas_provisioning:{company_id}"
    progress = frappe.cache().get_value(progress_key) or {}

    return ResponseFormatter.success(data={
        "company_id": doc.name,
        "status": doc.status,
        "steps": progress.get("steps", []),
        "current_step": progress.get("current_step", ""),
        "percent_complete": progress.get("percent_complete", 0),
        "started_at": doc.provisioning_started_at,
        "completed_at": doc.provisioning_completed_at,
        "error": progress.get("error"),
    })


@frappe.whitelist()
@handle_exceptions
def retry_provisioning(company_id):
    """Retry failed provisioning."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if doc.status != "Failed":
        return ResponseFormatter.validation_error(_("Only failed companies can be retried"))

    doc.db_set("status", "Provisioning", update_modified=True)
    doc.db_set("provisioning_started_at", now_datetime(), update_modified=False)
    frappe.db.commit()

    frappe.enqueue(
        "pix_one.api.companies.create_companies.provisioning_jobs.provision_company_site",
        queue="long",
        timeout=600,
        company_id=company_id,
        site_name=doc.site_name,
        admin_password=doc.get_password("admin_password") if doc.admin_password else "admin",
        admin_email=doc.admin_email,
        customer_email=doc.customer_id,
        apps_to_install=["erpnext"],
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(message=_("Provisioning retry started"))


# ==================== DOMAIN MANAGEMENT ====================

@frappe.whitelist()
@handle_exceptions
def set_custom_domain(company_id, custom_domain):
    """Set a custom domain for a company site."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if doc.status != "Active":
        return ResponseFormatter.validation_error(_("Company must be active to set custom domain"))

    # Validate domain format
    import re
    if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$', custom_domain.lower()):
        return ResponseFormatter.validation_error(_("Invalid domain format"))

    # Check if domain is already in use
    existing = frappe.db.get_value("SaaS Company", {"domain": custom_domain, "name": ["!=", company_id]}, "name")
    if existing:
        return ResponseFormatter.validation_error(_("Domain is already in use"))

    doc.db_set("domain", custom_domain, update_modified=True)
    frappe.db.commit()

    return ResponseFormatter.success(data={
        "company_id": doc.name,
        "custom_domain": custom_domain,
        "dns_records": [
            {"type": "CNAME", "name": custom_domain, "value": f"{doc.site_name}."},
            {"type": "A", "name": custom_domain, "value": "YOUR_SERVER_IP"}
        ],
        "message": _("Configure the DNS records above, then verify the domain.")
    })


@frappe.whitelist()
@handle_exceptions
def verify_domain(company_id):
    """Verify DNS configuration for a custom domain."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if not doc.domain:
        return ResponseFormatter.validation_error(_("No custom domain configured"))

    import socket
    try:
        resolved = socket.gethostbyname(doc.domain)
        verified = True
    except socket.gaierror:
        resolved = None
        verified = False

    return ResponseFormatter.success(data={
        "domain": doc.domain,
        "verified": verified,
        "resolved_ip": resolved,
        "message": _("Domain verified!") if verified else _("DNS not configured yet. Please add the required DNS records.")
    })


@frappe.whitelist()
@handle_exceptions
def remove_custom_domain(company_id):
    """Remove custom domain from a company."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    doc.db_set("domain", None, update_modified=True)
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Custom domain removed"))


# ==================== HEALTH & BACKUP ====================

@frappe.whitelist()
@handle_exceptions
def check_site_health(company_id):
    """Check health status of a company site."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if not doc.site_name:
        return ResponseFormatter.validation_error(_("No site configured"))

    site_path = Path(BENCH_PATH) / "sites" / doc.site_name
    health = {
        "site_exists": site_path.exists(),
        "site_name": doc.site_name,
        "status": doc.status,
    }

    if site_path.exists():
        code, out, err = _run_bench(["bench", "--site", doc.site_name, "doctor"])
        health["doctor_output"] = out
        health["is_healthy"] = code == 0

    return ResponseFormatter.success(data=health)


@frappe.whitelist()
@handle_exceptions
def get_site_metrics(company_id):
    """Get site resource metrics (DB size, etc.)."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    metrics = {"company_id": doc.name, "site_name": doc.site_name}

    # Get DB size
    try:
        db_name = doc.get("db_name") or f"_{doc.site_name.replace('.', '_')}"
        result = frappe.db.sql("""
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
            FROM information_schema.tables
            WHERE table_schema = %s
        """, db_name, as_dict=True)
        metrics["db_size_mb"] = float(result[0].size_mb) if result and result[0].size_mb else 0
    except Exception:
        metrics["db_size_mb"] = 0

    # Get file storage size
    site_path = Path(BENCH_PATH) / "sites" / doc.site_name
    if site_path.exists():
        try:
            code, out, _ = _run(f"du -sm {shlex.quote(str(site_path))} 2>/dev/null | cut -f1")
            metrics["storage_mb"] = float(out.strip()) if code == 0 and out.strip() else 0
        except Exception:
            metrics["storage_mb"] = 0

    return ResponseFormatter.success(data=metrics)


@frappe.whitelist()
@handle_exceptions
def create_backup(company_id):
    """Trigger a site backup."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if not doc.site_name:
        return ResponseFormatter.validation_error(_("No site configured"))

    frappe.enqueue(
        "pix_one.api.companies.backup.backup_jobs.run_backup",
        queue="long",
        timeout=600,
        company_id=company_id,
        site_name=doc.site_name,
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(
        message=_("Backup initiated. You will be notified when it completes.")
    )


@frappe.whitelist()
@handle_exceptions
def list_backups(company_id):
    """List available backups for a company."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    backups = frappe.get_all(
        "SaaS Site Backup",
        filters={"company_id": company_id},
        fields=["name", "backup_type", "file_size_mb", "status", "creation"],
        order_by="creation desc",
        page_length=20
    )

    return ResponseFormatter.success(data=backups)


@frappe.whitelist()
@handle_exceptions
def restore_backup(company_id, backup_id):
    """Restore a site from a backup."""
    doc = frappe.get_doc("SaaS Company", company_id)
    _check_permission(doc)

    if not frappe.db.exists("SaaS Site Backup", backup_id):
        return ResponseFormatter.not_found(_("Backup not found"))

    frappe.enqueue(
        "pix_one.api.companies.backup.backup_jobs.run_restore",
        queue="long",
        timeout=600,
        company_id=company_id,
        backup_id=backup_id,
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(
        message=_("Restore initiated. You will be notified when it completes.")
    )


@frappe.whitelist()
@handle_exceptions
def download_backup(backup_id):
    """Get download URL for a backup."""
    user = frappe.session.user
    backup = frappe.get_doc("SaaS Site Backup", backup_id)

    company = frappe.get_doc("SaaS Company", backup.company_id)
    _check_permission(company)

    return ResponseFormatter.success(data={
        "backup_id": backup.name,
        "download_url": backup.get("file_url"),
        "file_size_mb": backup.get("file_size_mb"),
        "created_at": backup.creation
    })
