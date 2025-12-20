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
BENCH_PATH = os.getenv("BENCH_PATH", "/workspace/development/saas-bench")


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


def _create_erpnext_company(
    site_name: str,
    company_name: str,
    company_abbr: str,
    default_currency: str = "USD",
    country: str = "United States"
) -> Tuple[bool, str, Optional[str]]:
    """
    Create an ERPNext Company on the provisioned site.

    Args:
        site_name: Name of the site
        company_name: Company name
        company_abbr: Company abbreviation
        default_currency: Default currency code
        country: Country name

    Returns:
        Tuple of (success, message, company_id)
    """
    try:
        # Create company via bench console
        script = f"""
import frappe
frappe.init(site='{site_name}')
frappe.connect()

company_doc = frappe.get_doc({{
    "doctype": "Company",
    "company_name": "{company_name}",
    "abbr": "{company_abbr}",
    "default_currency": "{default_currency}",
    "country": "{country}"
}})
company_doc.insert(ignore_permissions=True)
frappe.db.commit()

print(company_doc.name)
"""

        cmd = f"cd {shlex.quote(BENCH_PATH)} && echo {shlex.quote(script)} | bench --site {site_name} console"
        code, out, err = _run(cmd)

        if code == 0 and out.strip():
            company_id = out.strip().split('\n')[-1]  # Get last line (company name)
            return True, "ERPNext company created successfully", company_id
        else:
            return False, f"Failed to create ERPNext company: {err or out}", None

    except Exception as e:
        return False, f"Error creating ERPNext company: {str(e)}", None


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

@frappe.whitelist()
@handle_exceptions
def create_company(
    company_name: str,
    company_abbr: Optional[str] = None,
    admin_password: Optional[str] = None,
    admin_email: Optional[str] = None,
    default_currency: str = "USD",
    country: str = "United States",
    domain: Optional[str] = None,
    apps_to_install: Optional[list] = None,
    subscription_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new company with a dedicated Frappe site.

    Args:
        company_name: Name of the company
        company_abbr: Company abbreviation (auto-generated if not provided)
        admin_password: Admin password for the site (auto-generated if not provided)
        admin_email: Admin email (defaults to current user)
        default_currency: Default currency code
        country: Country name
        domain: Business domain/website (e.g., erp.acme.com)
        apps_to_install: List of apps to install (e.g., ['erpnext'])
        subscription_id: Subscription ID (auto-detected if not provided)

    Returns:
        Dictionary with company details and site information
    """
    # Get current user
    current_user = frappe.session.user
    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to create a company")

    # VALIDATE SUBSCRIPTION
    is_valid, error_msg, validated_subscription_id = _validate_subscription(current_user, subscription_id)
    if not is_valid:
        return ResponseFormatter.validation_error(
            error_msg,
            {"subscription": "INVALID_OR_INACTIVE"}
        )

    subscription_id = validated_subscription_id

    # VALIDATE COMPANY QUOTA
    quota_valid, quota_error = _validate_company_quota(subscription_id)
    if not quota_valid:
        return ResponseFormatter.validation_error(
            quota_error,
            {"quota": "EXCEEDED"}
        )

    # Validate company name
    if not company_name or len(company_name.strip()) < 3:
        return ResponseFormatter.validation_error(
            "Invalid company name",
            {"company_name": "Company name must be at least 3 characters"}
        )

    # Auto-generate company abbreviation
    if not company_abbr:
        import re
        # Take first 3-5 chars or initials
        words = company_name.strip().split()
        if len(words) > 1:
            company_abbr = ''.join([w[0].upper() for w in words[:5]])
        else:
            company_abbr = company_name[:5].upper()
        company_abbr = re.sub(r'[^A-Z0-9]', '', company_abbr)[:10]

    # Auto-generate admin password if not provided
    if not admin_password:
        import secrets
        admin_password = secrets.token_urlsafe(16)

    # Set admin email
    if not admin_email:
        admin_email = current_user

    # Parse apps_to_install
    if apps_to_install is None:
        apps_to_install = ["erpnext"]  # Default to ERPNext
    elif isinstance(apps_to_install, str):
        try:
            apps_to_install = json.loads(apps_to_install)
        except:
            apps_to_install = [app.strip() for app in apps_to_install.split(',') if app.strip()]

    # Create SaaS Company document
    try:
        company_doc = frappe.get_doc({
            "doctype": "SaaS Company",
            "company_name": company_name,
            "company_abbr": company_abbr,
            "customer_id": current_user,
            "subscription_id": subscription_id,
            "admin_password": admin_password,
            "admin_email": admin_email,
            "default_currency": default_currency,
            "country": country,
            "domain": domain,
            "status": "Draft"
        })

        company_doc.insert(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        frappe.db.rollback()
        return ResponseFormatter.error(
            f"Failed to create company record: {str(e)}",
            "COMPANY_CREATE_FAILED"
        )

    # Start provisioning
    site_name = company_doc.site_name

    try:
        # Update status to Provisioning
        company_doc.db_set("status", "Provisioning", update_modified=False)
        company_doc.db_set("provisioning_started_at", now_datetime(), update_modified=False)
        company_doc.db_set("site_status", "Creating", update_modified=False)
        frappe.db.commit()

        # Get DB config
        db_config = _get_db_config()

        # Provision Frappe site
        success, message, output = _provision_frappe_site(
            site_name,
            admin_password,
            db_config,
            overwrite=True
        )

        if not success:
            raise Exception(f"Site provisioning failed: {message}")

        company_doc.db_set("site_status", "Active", update_modified=False)
        company_doc.db_set("db_name", f"_{site_name}", update_modified=False)
        company_doc.db_set("db_host", db_config["db_host"], update_modified=False)
        company_doc.db_set("db_port", db_config["db_port"], update_modified=False)

        provisioning_notes = [f"Site created: {message}"]

        # Install apps
        if apps_to_install:
            app_success, app_message = _install_apps_on_site(site_name, apps_to_install)
            provisioning_notes.append(f"Apps: {app_message}")

            if not app_success:
                frappe.logger().warning(f"App installation issues: {app_message}")

        # Create ERPNext company if erpnext is installed
        if "erpnext" in apps_to_install:
            erp_success, erp_message, erp_company_id = _create_erpnext_company(
                site_name,
                company_name,
                company_abbr,
                default_currency,
                country
            )

            if erp_success and erp_company_id:
                company_doc.db_set("erpnext_company_id", erp_company_id, update_modified=False)
                company_doc.db_set("is_erpnext_synced", 1, update_modified=False)
                provisioning_notes.append(f"ERPNext company created: {erp_company_id}")
            else:
                provisioning_notes.append(f"ERPNext company creation failed: {erp_message}")

        # Update completion status
        company_doc.db_set("status", "Active", update_modified=False)
        company_doc.db_set("provisioning_completed_at", now_datetime(), update_modified=False)
        company_doc.db_set("provisioning_notes", "\n".join(provisioning_notes), update_modified=False)
        frappe.db.commit()

        # Reload document to get fresh data
        company_doc.reload()

        return ResponseFormatter.created(
            {
                "company_id": company_doc.name,
                "company_name": company_doc.company_name,
                "site_name": company_doc.site_name,
                "site_url": company_doc.site_url,
                "admin_email": company_doc.admin_email,
                "admin_password": admin_password,  # Return password only on creation
                "status": company_doc.status,
                "erpnext_company_id": company_doc.erpnext_company_id,
                "provisioning_notes": company_doc.provisioning_notes
            },
            f"Company '{company_name}' created successfully with site '{site_name}'"
        )

    except Exception as e:
        # Mark as failed
        try:
            company_doc.db_set("status", "Failed", update_modified=False)
            company_doc.db_set("provisioning_notes", f"Error: {str(e)}", update_modified=False)
            frappe.db.commit()
        except:
            pass

        frappe.log_error(f"Company creation failed: {str(e)}", "Company Creation Error")
        return ResponseFormatter.server_error(f"Company creation failed: {str(e)}")


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

        # Use the create_company function with existing details
        return create_company(
            company_name=company_doc.company_name,
            company_abbr=company_doc.company_abbr,
            admin_password=company_doc.get_password("admin_password"),
            admin_email=company_doc.admin_email,
            default_currency=company_doc.default_currency,
            country=company_doc.country,
            domain=company_doc.domain,
            subscription_id=company_doc.subscription_id
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
