"""
Company Creation Service for SaaS ERP Platform

This service handles the complete workflow of creating new companies with dedicated sites.
Each company gets its own Frappe site within the shared bench infrastructure.
"""

import os
import shlex
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import now, now_datetime, cstr

from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions


# Configuration
BENCH_PATH = os.getenv("BENCH_PATH", "/workspace/development/frappe-bench")


# ==================== UTILITY FUNCTIONS ====================

def _run(cmd: str) -> Tuple[int, str, str]:
    """Run a shell command with bash -lc, return (code, stdout, stderr)."""
    res = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, timeout=300)
    return res.returncode, res.stdout, res.stderr


def _run_bench(cmd_list: list) -> Tuple[int, str, str]:
    """Run a bench command within the BENCH_PATH directory."""
    if not os.path.isdir(BENCH_PATH):
        return 1, "", f"Bench path not found: {BENCH_PATH}"

    shell_cmd = f"cd {shlex.quote(BENCH_PATH)} && {shlex.join(cmd_list)}"
    return _run(shell_cmd)


def _site_path(site_name: str) -> Path:
    """Get the path to a site directory."""
    return Path(BENCH_PATH) / "sites" / site_name


def _site_lock(site_name: str) -> Path:
    """Get the path to the site lock file."""
    return _site_path(site_name) / "locks" / "bench_new_site.lock"


def _site_exists(site_name: str) -> bool:
    """Check if a site directory exists."""
    return _site_path(site_name).exists()


def _site_is_installed(site_name: str) -> bool:
    """Check if a site is fully installed and operational."""
    code, out, _ = _run_bench(["bench", "--site", site_name, "list-apps"])
    return code == 0


def _get_db_config() -> Dict[str, str]:
    """Get database configuration from environment or site_config."""
    return {
        "db_host": getattr(frappe.conf, "db_host", None) or os.getenv("DB_HOST") or "mariadb",
        "db_port": str(getattr(frappe.conf, "db_port", None) or os.getenv("DB_PORT") or "3306"),
        "db_root_user": getattr(frappe.conf, "db_root_username", None) or os.getenv("DB_ROOT_USER") or "root",
        "db_root_password": getattr(frappe.conf, "db_root_password", None) or os.getenv("DB_ROOT_PASSWORD") or ""
    }


def _clean_stale_lock(lock_file: Path) -> bool:
    """Clean stale lock file if it exists."""
    if lock_file.exists():
        try:
            # Check if bench new-site is actually running
            code, out, _ = _run("pgrep -af 'bench .* new-site' || true")
            if not out.strip():  # No process running
                lock_file.unlink(missing_ok=True)
                return True
        except Exception as e:
            frappe.log_error(f"Error cleaning lock file: {str(e)}")
    return False


# ==================== CORE SITE PROVISIONING ====================

def _provision_frappe_site(
    site_name: str,
    admin_password: str,
    db_config: Dict[str, str],
    overwrite: bool = True
) -> Tuple[bool, str, str]:
    """
    Provision a new Frappe site.

    Args:
        site_name: Name of the site to create
        admin_password: Password for the Administrator user
        db_config: Database configuration dictionary
        overwrite: Whether to overwrite existing partial sites

    Returns:
        Tuple of (success, message, output)
    """
    # Validate DB root password
    if not db_config.get("db_root_password"):
        return False, "DB root password not provided. Set DB_ROOT_PASSWORD env or site_config.", ""

    # Handle existing/partial site
    lock_file = _site_lock(site_name)
    if _site_exists(site_name) and not _site_is_installed(site_name):
        if not overwrite:
            return False, (
                f"Site folder '{site_name}' exists and seems partial. "
                f"Retry with overwrite=True or manually delete the site."
            ), ""

        # Clean stale lock
        _clean_stale_lock(lock_file)

    # Set global DB config for bench
    pre_cmd = f"""
        cd {shlex.quote(BENCH_PATH)} &&
        bench set-config -g db_host {shlex.quote(db_config['db_host'])} &&
        bench set-config -g db_port {shlex.quote(db_config['db_port'])}
    """
    pre_code, pre_out, pre_err = _run(pre_cmd)
    if pre_code != 0:
        return False, f"Failed to set DB config: {pre_err or pre_out}", ""

    # Create the site
    cmd = [
        "bench", "new-site", site_name,
        "--admin-password", admin_password,
        "--db-root-username", db_config["db_root_user"],
        "--db-root-password", db_config["db_root_password"],
        "--mariadb-user-host-login-scope", "%",  # Allow container IPs
        "--force",
    ]

    frappe.logger().info(f"Creating site: {site_name}")
    code, out, err = _run_bench(cmd)

    if code != 0:
        if "could not be acquired" in (err or out):
            return False, "Site creation lock conflict. Please retry.", ""
        return False, err or out, ""

    return True, f"Site {site_name} created successfully", out


def _install_apps_on_site(site_name: str, apps_to_install: list) -> Tuple[bool, str]:
    """
    Install specified apps on the site.

    Args:
        site_name: Name of the site
        apps_to_install: List of app names to install

    Returns:
        Tuple of (success, message)
    """
    if not apps_to_install:
        return True, "No apps to install"

    installed_apps = []
    failed_apps = []

    for app_name in apps_to_install:
        frappe.logger().info(f"Installing {app_name} on {site_name}")
        cmd = ["bench", "--site", site_name, "install-app", app_name]
        code, out, err = _run_bench(cmd)

        if code == 0:
            installed_apps.append(app_name)
        else:
            failed_apps.append({"app": app_name, "error": err or out})

    if failed_apps:
        return False, f"Failed to install apps: {json.dumps(failed_apps)}"

    return True, f"Installed apps: {', '.join(installed_apps)}"


# ==================== VALIDATION FUNCTIONS ====================

def _validate_subscription(user_id: str, subscription_id: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Validate that the user has an active subscription.

    Args:
        user_id: User ID to validate
        subscription_id: Optional subscription ID to use

    Returns:
        Tuple of (is_valid, error_message, subscription_id)
    """
    try:
        # If subscription_id provided, validate it belongs to user and is active
        if subscription_id:
            subscription = frappe.get_doc("SaaS Subscriptions", subscription_id)

            if subscription.customer_id != user_id:
                return False, "This subscription does not belong to you", None

            if subscription.status != "Active":
                return False, f"Subscription is {subscription.status}. Only Active subscriptions can create companies.", None

            return True, "", subscription_id

        # Otherwise, find an active subscription for the user
        active_subscription = frappe.db.get_value(
            "SaaS Subscriptions",
            {
                "customer_id": user_id,
                "status": "Active"
            },
            "name",
            order_by="creation desc"
        )

        if not active_subscription:
            return False, (
                "No active subscription found. Please purchase a subscription plan first."
            ), None

        return True, "", active_subscription

    except frappe.DoesNotExistError:
        return False, "Subscription not found", None
    except Exception as e:
        return False, f"Subscription validation error: {str(e)}", None


def _validate_company_quota(subscription_id: str, exclude_company_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate that the subscription has not exceeded company quota.

    Args:
        subscription_id: Subscription ID to check
        exclude_company_id: Company ID to exclude from count (for updates)

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        subscription = frappe.get_doc("SaaS Subscriptions", subscription_id)
        plan = frappe.get_doc("SaaS Subscription Plan", subscription.plan_name)

        max_companies = plan.max_companies or 1

        # Count existing active companies
        filters = {
            "subscription_id": subscription_id,
            "status": ["not in", ["Deleted", "Failed"]]
        }

        if exclude_company_id:
            filters["name"] = ["!=", exclude_company_id]

        existing_count = frappe.db.count("SaaS Company", filters)

        if existing_count >= max_companies:
            return False, (
                f"Company limit reached. Your '{plan.plan_name}' plan allows {max_companies} "
                f"{'company' if max_companies == 1 else 'companies'}. "
                f"You currently have {existing_count}. Please upgrade your subscription."
            )

        return True, ""

    except Exception as e:
        return False, f"Quota validation error: {str(e)}"


# ==================== MAIN API ENDPOINTS ====================

def _get_base_domain() -> str:
    """Get the configured base domain from PixOne System Settings."""
    try:
        return (frappe.db.get_single_value("PixOne System Settings", "base_domain") or "pixone.com").strip().lower().rstrip(".")
    except Exception:
        return "pixone.com"


def _validate_subdomain(subdomain: str) -> Tuple[bool, str]:
    """
    Validate and enforce subdomain uniqueness.
    Returns (is_valid, error_message).
    """
    import re as _re

    slug = (subdomain or "").strip().lower()

    if len(slug) < 3:
        return False, "Subdomain must be at least 3 characters."

    if len(slug) > 63:
        return False, "Subdomain cannot exceed 63 characters."

    if not _re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', slug):
        return False, (
            "Subdomain may only contain lowercase letters, numbers, and hyphens, "
            "and must start and end with a letter or number."
        )

    # Check reserved list
    from pix_one.api.companies.domain.domain_service import _BUILTIN_RESERVED, _get_settings
    _, _, reserved = _get_settings()
    if slug in reserved:
        return False, f"'{slug}' is a reserved subdomain name."

    # Uniqueness: ensure no active company uses this subdomain
    taken = frappe.db.exists("SaaS Company", {
        "subdomain": slug,
        "status": ["not in", ["Deleted", "Failed"]]
    })
    if taken:
        return False, f"The subdomain '{slug}' is already taken. Please choose a different one."

    return True, ""


@frappe.whitelist()
@handle_exceptions
def create_company(
    company_name: str,
    subdomain: str,
    company_abbr: Optional[str] = None,
    admin_password: Optional[str] = None,
    admin_email: Optional[str] = None,
    default_currency: str = "BDT",
    country: str = "Bangladesh",
    apps_to_install: Optional[list] = ["erpnext"],
    subscription_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new company with a dedicated Frappe site.

    Args:
        company_name:     Human-readable company name  (e.g. "Pixfar Technologies")
        subdomain:        Unique subdomain slug         (e.g. "pixfar")
                          → full site will be  pixfar.pixone.com
        company_abbr:     Abbreviation (auto-generated if omitted)
        admin_password:   Site admin password (auto-generated if omitted)
        admin_email:      Site admin email (defaults to current user)
        default_currency: ISO currency code
        country:          Country name
        apps_to_install:  Apps to install on the new site (default: ['erpnext'])
        subscription_id:  Subscription to bill against (auto-detected if omitted)

    Returns:
        {
            "company_id": "COMP-2026-00001",
            "company_name": "Pixfar Technologies",
            "subdomain": "pixfar",
            "site_name": "pixfar.pixone.com",
            "site_url": "https://pixfar.pixone.com",
            "status": "Queued"
        }
    """
    # ── Auth ─────────────────────────────────────────────────────────────────
    current_user = frappe.session.user
    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to create a company.")

    # ── Subdomain validation (first – cheapest check) ────────────────────────
    if not subdomain:
        return ResponseFormatter.validation_error(
            "Subdomain is required.",
            {"subdomain": "Please provide a subdomain for your company site."}
        )

    slug = subdomain.strip().lower()
    sub_valid, sub_error = _validate_subdomain(slug)
    if not sub_valid:
        return ResponseFormatter.validation_error(sub_error, {"subdomain": sub_error})

    # ── Company name validation ──────────────────────────────────────────────
    if not company_name or len(company_name.strip()) < 3:
        return ResponseFormatter.validation_error(
            "Company name must be at least 3 characters.",
            {"company_name": "Too short"}
        )

    # ── Subscription validation ──────────────────────────────────────────────
    is_valid, error_msg, validated_subscription_id = _validate_subscription(current_user, subscription_id)
    if not is_valid:
        return ResponseFormatter.validation_error(error_msg, {"subscription": "INVALID_OR_INACTIVE"})

    subscription_id = validated_subscription_id

    # ── Quota check ──────────────────────────────────────────────────────────
    quota_valid, quota_error = _validate_company_quota(subscription_id)
    if not quota_valid:
        return ResponseFormatter.validation_error(quota_error, {"quota": "EXCEEDED"})

    # ── Derived values ───────────────────────────────────────────────────────
    base_domain = _get_base_domain()
    site_name = f"{slug}.{base_domain}"
    site_url = f"https://{site_name}"

    if not company_abbr:
        import re as _re
        words = company_name.strip().split()
        if len(words) > 1:
            company_abbr = "".join([w[0].upper() for w in words[:5]])
        else:
            company_abbr = company_name[:5].upper()
        company_abbr = _re.sub(r"[^A-Z0-9]", "", company_abbr)[:10]

    if not admin_password:
        import secrets
        admin_password = secrets.token_urlsafe(16)

    if not admin_email:
        admin_email = current_user

    if apps_to_install is None:
        apps_to_install = ["erpnext"]
    elif isinstance(apps_to_install, str):
        try:
            apps_to_install = json.loads(apps_to_install)
        except Exception:
            apps_to_install = [a.strip() for a in apps_to_install.split(",") if a.strip()]

    # ── Create SaaS Company document ─────────────────────────────────────────
    try:
        company_doc = frappe.get_doc({
            "doctype": "SaaS Company",
            "company_name": company_name,
            "company_abbr": company_abbr,
            "subdomain": slug,
            "site_name": site_name,
            "site_url": site_url,
            "customer_id": current_user,
            "subscription_id": subscription_id,
            "admin_password": admin_password,
            "admin_email": admin_email,
            "default_currency": default_currency,
            "country": country,
            "status": "Draft"
        })

        company_doc.insert(ignore_permissions=True)
        frappe.db.commit()

    except frappe.UniqueValidationError:
        frappe.db.rollback()
        return ResponseFormatter.validation_error(
            f"The subdomain '{slug}' was just registered by someone else. Please choose another.",
            {"subdomain": "RACE_CONDITION"}
        )
    except Exception as e:
        frappe.db.rollback()
        return ResponseFormatter.error(
            f"Failed to create company record: {str(e)}",
            "COMPANY_CREATE_FAILED"
        )

    # ── Queue provisioning ───────────────────────────────────────────────────
    try:
        company_doc.db_set("status", "Queued", update_modified=False)
        company_doc.db_set("site_status", "Queued", update_modified=False)
        frappe.db.commit()

        frappe.enqueue(
            "pix_one.api.companies.create_companies.provisioning_jobs.provision_company_site",
            queue="long",
            timeout=600,
            company_id=company_doc.name,
            site_name=site_name,
            admin_password=admin_password,
            admin_email=admin_email,
            customer_email=current_user,
            apps_to_install=apps_to_install,
            is_async=True,
            now=False
        )

        frappe.logger().info(f"Provisioning job enqueued for company {company_doc.name} → {site_name}")

        return ResponseFormatter.created(
            {
                "company_id": company_doc.name,
                "company_name": company_doc.company_name,
                "subdomain": slug,
                "site_name": site_name,
                "site_url": site_url,
                "status": "Queued",
                "message": (
                    f"Company created. Your site '{site_name}' is being provisioned. "
                    "You will receive an email with login credentials once it's ready."
                )
            },
            f"Company '{company_name}' created. Provisioning in progress..."
        )

    except Exception as e:
        try:
            company_doc.db_set("status", "Failed", update_modified=False)
            company_doc.db_set("provisioning_notes", f"Queue error: {str(e)}", update_modified=False)
            frappe.db.commit()
        except Exception:
            pass

        frappe.log_error(f"Company creation failed: {str(e)}", "Company Creation Error")
        return ResponseFormatter.server_error(f"Company creation failed: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def get_company_status(company_id: str) -> Dict[str, Any]:
    """
    Get the provisioning status of a company.

    Args:
        company_id: ID of the company

    Returns:
        Dictionary with company status details
    """
    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permissions
        if frappe.session.user != company_doc.customer_id and not frappe.has_permission("SaaS Company", "read"):
            return ResponseFormatter.forbidden("You don't have permission to view this company")

        return ResponseFormatter.success(
            {
                "company_id": company_doc.name,
                "company_name": company_doc.company_name,
                "status": company_doc.status,
                "site_status": company_doc.site_status,
                "site_name": company_doc.site_name,
                "site_url": company_doc.site_url,
                "provisioning_started_at": company_doc.provisioning_started_at,
                "provisioning_completed_at": company_doc.provisioning_completed_at,
                "provisioning_notes": company_doc.provisioning_notes
            },
            f"Status: {company_doc.status}"
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        return ResponseFormatter.server_error(f"Failed to get status: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def retry_failed_company(company_id: str) -> Dict[str, Any]:
    """
    Retry provisioning for a failed company.

    Args:
        company_id: ID of the failed company

    Returns:
        Dictionary with retry status
    """
    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        if company_doc.status != "Failed":
            return ResponseFormatter.validation_error(
                "Only failed companies can be retried",
                {"status": company_doc.status}
            )

        # Re-queue provisioning directly (subdomain already locked in the existing doc)
        site_name = company_doc.site_name
        admin_password = company_doc.get_password("admin_password") or "admin"

        company_doc.db_set("status", "Queued", update_modified=False)
        company_doc.db_set("site_status", "Queued", update_modified=False)
        company_doc.db_set("provisioning_notes", "", update_modified=False)
        frappe.db.commit()

        frappe.enqueue(
            "pix_one.api.companies.create_companies.provisioning_jobs.provision_company_site",
            queue="long",
            timeout=600,
            company_id=company_doc.name,
            site_name=site_name,
            admin_password=admin_password,
            admin_email=company_doc.admin_email,
            customer_email=company_doc.customer_id,
            apps_to_install=["erpnext"],
            is_async=True,
            now=False
        )

        return ResponseFormatter.success(
            data={
                "company_id": company_doc.name,
                "subdomain": company_doc.subdomain,
                "site_name": site_name,
                "status": "Queued"
            },
            message=f"Retry queued for company '{company_doc.company_name}'."
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        return ResponseFormatter.server_error(f"Retry failed: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def delete_company(company_id: str, drop_site: bool = False) -> Dict[str, Any]:
    """
    Delete a company and optionally drop its site.

    Args:
        company_id: ID of the company to delete
        drop_site: Whether to drop the Frappe site

    Returns:
        Dictionary with deletion status
    """
    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permissions
        if frappe.session.user != company_doc.customer_id and not frappe.has_permission("SaaS Company", "delete"):
            return ResponseFormatter.forbidden("You don't have permission to delete this company")

        site_name = company_doc.site_name

        # Drop the site if requested and it exists
        if drop_site and _site_exists(site_name):
            db_config = _get_db_config()
            cmd = [
                "bench", "drop-site", site_name,
                "--force",
                "--no-backup",
                "--mariadb-root-password", db_config["db_root_password"]
            ]

            code, out, err = _run_bench(cmd)
            if code != 0:
                frappe.log_error(f"Failed to drop site {site_name}: {err}")

        # Mark as deleted
        company_doc.db_set("status", "Deleted", update_modified=False)
        company_doc.db_set("deletion_requested_at", now_datetime(), update_modified=False)
        company_doc.db_set("site_status", "Deleted", update_modified=False)
        frappe.db.commit()

        # Delete the document
        frappe.delete_doc("SaaS Company", company_id, ignore_permissions=True)
        frappe.db.commit()

        return ResponseFormatter.deleted(
            f"Company {company_doc.company_name} deleted successfully" +
            (f" and site {site_name} dropped" if drop_site else "")
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        frappe.db.rollback()
        return ResponseFormatter.server_error(f"Deletion failed: {str(e)}")
