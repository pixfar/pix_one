"""
Module 9: Monitoring & Observability - Health checks, Metrics, Alerts, Logs
"""

import os
import shlex
import subprocess
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now_datetime
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions

BENCH_PATH = os.getenv("BENCH_PATH", "/workspace/development/frappe-bench")


def _require_admin():
    if "System Manager" not in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Admin access required"), frappe.PermissionError)


@frappe.whitelist()
@handle_exceptions
def platform_health():
    """Overall platform health check."""
    _require_admin()

    checks = {}

    # Database check
    try:
        frappe.db.sql("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        frappe.cache().set_value("health_check", "ok", expires_in_sec=5)
        checks["redis"] = {"status": "healthy"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Worker check
    try:
        result = frappe.db.sql("""
            SELECT status, COUNT(*) as count FROM `tabRQ Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY status
        """, as_dict=True)
        checks["workers"] = {"status": "healthy", "recent_jobs": result}
    except Exception:
        checks["workers"] = {"status": "unknown"}

    # Disk check
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        disk_usage_pct = round((used / total) * 100, 1)
        checks["disk"] = {
            "status": "healthy" if disk_usage_pct < 90 else "warning",
            "usage_percent": disk_usage_pct,
            "free_gb": round(free / (1024**3), 2)
        }
    except Exception:
        checks["disk"] = {"status": "unknown"}

    overall = "healthy" if all(c.get("status") == "healthy" for c in checks.values()) else "degraded"

    return ResponseFormatter.success(data={"overall": overall, "checks": checks, "timestamp": str(now_datetime())})


@frappe.whitelist()
@handle_exceptions
def site_health(company_id):
    """Individual site health check."""
    doc = frappe.get_doc("SaaS Company", company_id)
    user = frappe.session.user
    if user != doc.customer_id and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    health = {"site_name": doc.site_name, "status": doc.status}

    site_path = Path(BENCH_PATH) / "sites" / doc.site_name
    health["site_exists"] = site_path.exists()

    if site_path.exists():
        res = subprocess.run(
            ["bash", "-lc", f"cd {shlex.quote(BENCH_PATH)} && bench --site {shlex.quote(doc.site_name)} doctor"],
            capture_output=True, text=True, timeout=30
        )
        health["is_healthy"] = res.returncode == 0
        health["details"] = res.stdout.strip() if res.returncode == 0 else res.stderr.strip()

    return ResponseFormatter.success(data=health)


@frappe.whitelist()
@handle_exceptions
def get_site_metrics(company_id):
    """Get site resource metrics."""
    doc = frappe.get_doc("SaaS Company", company_id)
    user = frappe.session.user
    if user != doc.customer_id and "System Manager" not in frappe.get_roles(user):
        return ResponseFormatter.forbidden(_("Access denied"))

    metrics = {"site_name": doc.site_name}

    # DB size
    try:
        result = frappe.db.sql("""
            SELECT ROUND(SUM(data_length + index_length)/1024/1024, 2) AS size_mb
            FROM information_schema.tables
            WHERE table_schema LIKE %s
        """, f"%{doc.site_name.replace('.', '_')}%", as_dict=True)
        metrics["db_size_mb"] = float(result[0].size_mb) if result and result[0].size_mb else 0
    except Exception:
        metrics["db_size_mb"] = 0

    return ResponseFormatter.success(data=metrics)


@frappe.whitelist()
@handle_exceptions
def get_cluster_metrics():
    """Get overall cluster resource utilization."""
    _require_admin()

    metrics = {}

    # Total active sites
    metrics["active_sites"] = frappe.db.count("SaaS Company", {"status": "Active"})

    # Total DB size
    try:
        result = frappe.db.sql("""
            SELECT ROUND(SUM(data_length + index_length)/1024/1024/1024, 2) AS total_gb
            FROM information_schema.tables
        """, as_dict=True)
        metrics["total_db_gb"] = float(result[0].total_gb) if result and result[0].total_gb else 0
    except Exception:
        metrics["total_db_gb"] = 0

    # Job stats
    metrics["jobs_last_hour"] = frappe.db.count("RQ Job", {
        "creation": [">=", frappe.utils.add_to_date(now_datetime(), hours=-1)]
    })

    return ResponseFormatter.success(data=metrics)


# ==================== ALERTS ====================

@frappe.whitelist()
@handle_exceptions
def get_active_alerts():
    """Get current active alerts."""
    _require_admin()

    alerts = frappe.get_all(
        "SaaS Alert Rule",
        filters={"is_active": 1, "last_triggered": ["is", "set"]},
        fields=["name", "alert_type", "severity", "message", "last_triggered", "trigger_count"],
        order_by="last_triggered desc"
    )

    return ResponseFormatter.success(data=alerts)


@frappe.whitelist()
@handle_exceptions
def configure_alert(alert_type, condition, severity="warning", message=None, is_active=1):
    """Create or update an alert rule."""
    _require_admin()

    existing = frappe.db.exists("SaaS Alert Rule", {"alert_type": alert_type})
    if existing:
        rule = frappe.get_doc("SaaS Alert Rule", existing)
        rule.condition = condition
        rule.severity = severity
        rule.message = message
        rule.is_active = int(is_active)
        rule.save(ignore_permissions=True)
    else:
        rule = frappe.get_doc({
            "doctype": "SaaS Alert Rule",
            "alert_type": alert_type,
            "condition": condition,
            "severity": severity,
            "message": message,
            "is_active": int(is_active)
        })
        rule.insert(ignore_permissions=True)

    frappe.db.commit()
    return ResponseFormatter.success(data={"alert_id": rule.name})


@frappe.whitelist()
@handle_exceptions
def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    _require_admin()

    rule = frappe.get_doc("SaaS Alert Rule", alert_id)
    rule.db_set("acknowledged_by", frappe.session.user)
    rule.db_set("acknowledged_at", now_datetime())
    frappe.db.commit()

    return ResponseFormatter.success(message=_("Alert acknowledged"))


# ==================== LOGS ====================

@frappe.whitelist()
@handle_exceptions
def get_error_logs(page=1, limit=50, site=None):
    """Get aggregated error logs."""
    _require_admin()
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {}
    if site:
        filters["method"] = ["like", f"%{site}%"]

    logs = frappe.get_all(
        "Error Log",
        filters=filters,
        fields=["name", "method", "error", "creation"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("Error Log", filters)

    return ResponseFormatter.paginated(data=logs, total=total, page=page, limit=limit)


@frappe.whitelist()
@handle_exceptions
def get_access_logs(page=1, limit=50, user=None):
    """Get API access logs."""
    _require_admin()
    page = int(page)
    limit = min(int(limit), 100)
    offset = (page - 1) * limit

    filters = {}
    if user:
        filters["user"] = user

    logs = frappe.get_all(
        "Access Log",
        filters=filters,
        fields=["name", "user", "doctype", "document", "method", "creation"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("Access Log", filters)

    return ResponseFormatter.paginated(data=logs, total=total, page=page, limit=limit)
