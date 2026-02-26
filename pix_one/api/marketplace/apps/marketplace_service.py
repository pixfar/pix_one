"""
Module 6: App Marketplace - App Installation, Management, and Reviews
"""

import os
import shlex
import subprocess
import json

import frappe
from frappe import _
from frappe.utils import now_datetime
from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions

BENCH_PATH = os.getenv("BENCH_PATH", "/workspace/development/frappe-bench")


def _run_bench(cmd_list, timeout=300):
    if not os.path.isdir(BENCH_PATH):
        return 1, "", f"Bench path not found: {BENCH_PATH}"
    shell_cmd = f"cd {shlex.quote(BENCH_PATH)} && {shlex.join(cmd_list)}"
    res = subprocess.run(["bash", "-lc", shell_cmd], capture_output=True, text=True, timeout=timeout)
    return res.returncode, res.stdout, res.stderr


def _check_company_permission(company_id):
    doc = frappe.get_doc("SaaS Company", company_id)
    user = frappe.session.user
    if user != doc.customer_id and "System Manager" not in frappe.get_roles(user):
        frappe.throw(_("Access denied"), frappe.PermissionError)
    return doc


@frappe.whitelist()
@handle_exceptions
def list_available_apps():
    """List all apps available in the marketplace."""
    apps = frappe.get_all(
        "SaaS App Registry",
        filters={"is_published": 1},
        fields=[
            "name", "app_name", "app_title", "description", "category",
            "icon_url", "price", "is_free", "developer", "version",
            "avg_rating", "total_installs", "frappe_version_compatibility"
        ],
        order_by="total_installs desc"
    )
    return ResponseFormatter.success(data=apps)


@frappe.whitelist()
@handle_exceptions
def get_app_details(app_name):
    """Get detailed app information, screenshots, and reviews."""
    if not frappe.db.exists("SaaS App Registry", {"app_name": app_name}):
        return ResponseFormatter.not_found(_("App not found"))

    app = frappe.get_doc("SaaS App Registry", {"app_name": app_name})

    screenshots = [{"url": s.url, "caption": s.caption} for s in app.get("screenshots", [])]

    reviews = frappe.get_all(
        "SaaS App Review",
        filters={"app_name": app_name},
        fields=["user", "rating", "review_text", "creation"],
        order_by="creation desc",
        page_length=10
    )

    return ResponseFormatter.success(data={
        "app_name": app.app_name,
        "app_title": app.app_title,
        "description": app.description,
        "long_description": app.get("long_description"),
        "category": app.category,
        "price": app.price,
        "is_free": app.is_free,
        "developer": app.developer,
        "version": app.version,
        "icon_url": app.icon_url,
        "avg_rating": app.avg_rating,
        "total_installs": app.total_installs,
        "screenshots": screenshots,
        "reviews": reviews,
    })


@frappe.whitelist()
@handle_exceptions
def get_installed_apps(company_id):
    """Get apps installed on a user's site."""
    doc = _check_company_permission(company_id)

    if not doc.site_name:
        return ResponseFormatter.validation_error(_("No site configured"))

    code, out, err = _run_bench(["bench", "--site", doc.site_name, "list-apps"])

    if code != 0:
        return ResponseFormatter.server_error(_("Failed to list apps: {0}").format(err))

    installed = []
    for line in out.strip().splitlines():
        if line.strip():
            parts = line.strip().split()
            installed.append({
                "app_name": parts[0],
                "version": parts[1] if len(parts) > 1 else "unknown",
                "branch": parts[2] if len(parts) > 2 else "unknown"
            })

    return ResponseFormatter.success(data={"company_id": company_id, "apps": installed})


@frappe.whitelist()
@handle_exceptions
def install_app(company_id, app_name):
    """Install an app on a company's site (async with migration)."""
    doc = _check_company_permission(company_id)

    if doc.status != "Active":
        return ResponseFormatter.validation_error(_("Company must be active to install apps"))

    if not doc.site_name:
        return ResponseFormatter.validation_error(_("No site configured"))

    # Enqueue installation job
    job_id = f"install_app_{company_id}_{app_name}"
    frappe.enqueue(
        "pix_one.api.marketplace.apps.marketplace_service._run_install_app",
        queue="long",
        timeout=600,
        job_id=job_id,
        deduplicate=True,
        company_id=company_id,
        site_name=doc.site_name,
        app_name=app_name,
        enqueue_after_commit=True
    )

    # Track status in Redis
    frappe.cache().set_value(f"app_install:{job_id}", {
        "status": "queued",
        "app_name": app_name,
        "company_id": company_id,
        "started_at": str(now_datetime())
    }, expires_in_sec=1800)

    return ResponseFormatter.success(data={
        "job_id": job_id,
        "status": "queued",
        "message": _("App installation queued. Migration will run automatically.")
    })


def _run_install_app(company_id, site_name, app_name):
    """Background job: Install app and run migration."""
    job_id = f"install_app_{company_id}_{app_name}"
    cache_key = f"app_install:{job_id}"

    try:
        frappe.cache().set_value(cache_key, {
            "status": "installing", "app_name": app_name, "company_id": company_id
        }, expires_in_sec=1800)

        # Install the app
        code, out, err = _run_bench(
            ["bench", "--site", site_name, "install-app", app_name], timeout=600
        )

        if code != 0:
            frappe.cache().set_value(cache_key, {
                "status": "failed", "error": err or out, "app_name": app_name
            }, expires_in_sec=1800)
            frappe.log_error(f"App install failed: {err}", "Marketplace Install Error")
            return

        # Run migration
        frappe.cache().set_value(cache_key, {
            "status": "migrating", "app_name": app_name, "company_id": company_id
        }, expires_in_sec=1800)

        code, out, err = _run_bench(
            ["bench", "--site", site_name, "migrate"], timeout=600
        )

        status = "completed" if code == 0 else "migration_failed"
        frappe.cache().set_value(cache_key, {
            "status": status, "app_name": app_name, "company_id": company_id
        }, expires_in_sec=1800)

        # Update install count
        if status == "completed" and frappe.db.exists("SaaS App Registry", {"app_name": app_name}):
            frappe.db.sql("""
                UPDATE `tabSaaS App Registry`
                SET total_installs = COALESCE(total_installs, 0) + 1
                WHERE app_name = %s
            """, app_name)

        frappe.db.commit()

    except Exception as e:
        frappe.cache().set_value(cache_key, {
            "status": "failed", "error": str(e), "app_name": app_name
        }, expires_in_sec=1800)
        frappe.log_error(frappe.get_traceback(), "Marketplace Install Error")


@frappe.whitelist()
@handle_exceptions
def uninstall_app(company_id, app_name):
    """Uninstall an app from a company's site (async with migration)."""
    doc = _check_company_permission(company_id)

    if app_name == "frappe":
        return ResponseFormatter.validation_error(_("Cannot uninstall the frappe framework"))

    job_id = f"uninstall_app_{company_id}_{app_name}"
    frappe.enqueue(
        "pix_one.api.marketplace.apps.marketplace_service._run_uninstall_app",
        queue="long",
        timeout=600,
        job_id=job_id,
        deduplicate=True,
        company_id=company_id,
        site_name=doc.site_name,
        app_name=app_name,
        enqueue_after_commit=True
    )

    frappe.cache().set_value(f"app_install:{job_id}", {
        "status": "queued", "action": "uninstall", "app_name": app_name
    }, expires_in_sec=1800)

    return ResponseFormatter.success(data={
        "job_id": job_id,
        "status": "queued",
        "message": _("App uninstallation queued.")
    })


def _run_uninstall_app(company_id, site_name, app_name):
    """Background job: Uninstall app and run migration."""
    job_id = f"uninstall_app_{company_id}_{app_name}"
    cache_key = f"app_install:{job_id}"

    try:
        code, out, err = _run_bench(
            ["bench", "--site", site_name, "uninstall-app", app_name, "--yes"], timeout=600
        )

        if code != 0:
            frappe.cache().set_value(cache_key, {
                "status": "failed", "error": err or out
            }, expires_in_sec=1800)
            return

        # Run migration
        code, out, err = _run_bench(
            ["bench", "--site", site_name, "migrate"], timeout=600
        )

        frappe.cache().set_value(cache_key, {
            "status": "completed" if code == 0 else "migration_failed"
        }, expires_in_sec=1800)
        frappe.db.commit()

    except Exception as e:
        frappe.cache().set_value(cache_key, {
            "status": "failed", "error": str(e)
        }, expires_in_sec=1800)
        frappe.log_error(frappe.get_traceback(), "Marketplace Uninstall Error")


@frappe.whitelist()
@handle_exceptions
def get_install_status(job_id):
    """Get installation/uninstallation progress."""
    cache_key = f"app_install:{job_id}"
    status = frappe.cache().get_value(cache_key)

    if not status:
        return ResponseFormatter.not_found(_("Job not found or expired"))

    return ResponseFormatter.success(data=status)


@frappe.whitelist()
@handle_exceptions
def update_app(company_id, app_name):
    """Update an app to the latest version on a site."""
    doc = _check_company_permission(company_id)

    job_id = f"update_app_{company_id}_{app_name}"
    frappe.enqueue(
        "pix_one.api.marketplace.apps.marketplace_service._run_update_app",
        queue="long",
        timeout=600,
        job_id=job_id,
        deduplicate=True,
        company_id=company_id,
        site_name=doc.site_name,
        app_name=app_name,
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(data={"job_id": job_id, "status": "queued"})


def _run_update_app(company_id, site_name, app_name):
    """Background job: Update app and migrate."""
    job_id = f"update_app_{company_id}_{app_name}"
    cache_key = f"app_install:{job_id}"

    try:
        # Pull latest
        code, out, err = _run_bench(["bench", "get-app", "--overwrite", app_name], timeout=600)
        if code != 0:
            frappe.cache().set_value(cache_key, {"status": "failed", "error": err}, expires_in_sec=1800)
            return

        # Migrate
        code, out, err = _run_bench(["bench", "--site", site_name, "migrate"], timeout=600)
        frappe.cache().set_value(cache_key, {
            "status": "completed" if code == 0 else "migration_failed"
        }, expires_in_sec=1800)
        frappe.db.commit()

    except Exception as e:
        frappe.cache().set_value(cache_key, {"status": "failed", "error": str(e)}, expires_in_sec=1800)


@frappe.whitelist()
@handle_exceptions
def update_all_apps(company_id):
    """Update all apps on a site."""
    doc = _check_company_permission(company_id)

    job_id = f"update_all_{company_id}"
    frappe.enqueue(
        "pix_one.api.marketplace.apps.marketplace_service._run_update_all",
        queue="long",
        timeout=900,
        job_id=job_id,
        deduplicate=True,
        site_name=doc.site_name,
        enqueue_after_commit=True
    )

    return ResponseFormatter.success(data={"job_id": job_id, "status": "queued"})


def _run_update_all(site_name):
    """Background job: Update all apps and migrate."""
    try:
        _run_bench(["bench", "update", "--site", site_name, "--reset"], timeout=900)
    except Exception as e:
        frappe.log_error(str(e), "Update All Apps Error")


@frappe.whitelist()
@handle_exceptions
def check_updates(company_id):
    """Check for available app updates on a site."""
    doc = _check_company_permission(company_id)

    code, out, err = _run_bench(["bench", "--site", doc.site_name, "list-apps"])
    if code != 0:
        return ResponseFormatter.server_error(_("Failed to check apps"))

    apps = []
    for line in out.strip().splitlines():
        if line.strip():
            parts = line.strip().split()
            apps.append({
                "app_name": parts[0],
                "current_version": parts[1] if len(parts) > 1 else "unknown",
                "branch": parts[2] if len(parts) > 2 else "unknown",
                "update_available": False  # Placeholder: would need git remote check
            })

    return ResponseFormatter.success(data={"apps": apps})


@frappe.whitelist()
@handle_exceptions
def get_app_compatibility(app_name, company_id):
    """Check if an app is compatible with a site's Frappe version."""
    doc = _check_company_permission(company_id)

    code, out, _ = _run_bench(["bench", "--site", doc.site_name, "version"])
    frappe_version = out.strip() if code == 0 else "unknown"

    compatible = True  # Default assumption
    if frappe.db.exists("SaaS App Registry", {"app_name": app_name}):
        app_reg = frappe.get_doc("SaaS App Registry", {"app_name": app_name})
        if app_reg.frappe_version_compatibility:
            compatible = frappe_version.startswith(app_reg.frappe_version_compatibility.split(".")[0])

    return ResponseFormatter.success(data={
        "app_name": app_name,
        "site_frappe_version": frappe_version,
        "compatible": compatible
    })


# ==================== REVIEWS ====================

@frappe.whitelist()
@handle_exceptions
def submit_review(app_name, rating, review_text=None):
    """Submit a review for an app."""
    user = frappe.session.user

    if not 1 <= int(rating) <= 5:
        return ResponseFormatter.validation_error(_("Rating must be between 1 and 5"))

    # Check if user already reviewed
    existing = frappe.db.exists("SaaS App Review", {"app_name": app_name, "user": user})
    if existing:
        # Update existing review
        review = frappe.get_doc("SaaS App Review", existing)
        review.rating = int(rating)
        review.review_text = review_text
        review.save(ignore_permissions=True)
    else:
        review = frappe.get_doc({
            "doctype": "SaaS App Review",
            "app_name": app_name,
            "user": user,
            "rating": int(rating),
            "review_text": review_text
        })
        review.insert(ignore_permissions=True)

    # Update average rating
    avg = frappe.db.sql("""
        SELECT AVG(rating) as avg_rating FROM `tabSaaS App Review` WHERE app_name = %s
    """, app_name, as_dict=True)
    if avg and avg[0].avg_rating:
        frappe.db.set_value("SaaS App Registry", {"app_name": app_name}, "avg_rating", avg[0].avg_rating)

    frappe.db.commit()

    return ResponseFormatter.success(message=_("Review submitted"))


@frappe.whitelist()
@handle_exceptions
def get_reviews(app_name, page=1, limit=20):
    """Get reviews for an app."""
    page = int(page)
    limit = min(int(limit), 50)
    offset = (page - 1) * limit

    reviews = frappe.get_all(
        "SaaS App Review",
        filters={"app_name": app_name},
        fields=["name", "user", "rating", "review_text", "creation"],
        order_by="creation desc",
        start=offset,
        page_length=limit
    )

    total = frappe.db.count("SaaS App Review", {"app_name": app_name})

    return ResponseFormatter.paginated(data=reviews, total=total, page=page, limit=limit)
