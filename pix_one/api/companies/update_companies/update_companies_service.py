"""
Company Update Service for SaaS ERP Platform

This service handles updating company details and renaming sites.
"""

import os
import shlex
import subprocess
from typing import Dict, Any, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import now_datetime

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


def _verify_user_password(user_email: str, password: str) -> bool:
    """
    Verify the password for the current user.

    Args:
        user_email: User's email address
        password: Password to verify

    Returns:
        True if password is correct, False otherwise
    """
    try:
        # Use Frappe's check_password function to verify
        from frappe.auth import check_password

        check_password(user_email, password)
        return True

    except frappe.exceptions.AuthenticationError:
        return False
    except Exception as e:
        frappe.log_error(f"Password verification error: {str(e)}", "Password Verification Error")
        return False


def _rename_site(old_site_name: str, new_site_name: str, company_doc) -> Tuple[bool, str]:
    """
    Rename a Frappe site using manual database and filesystem operations.

    Args:
        old_site_name: Current site name
        new_site_name: New site name
        company_doc: Company document (to get admin password)

    Returns:
        Tuple of (success, message)
    """
    try:
        # Get DB config
        from pix_one.api.companies.create_companies.create_companies_service import _get_db_config
        db_config = _get_db_config()

        # Step 2: Move site directory
        move_cmd = [
            "mv",
            f"{BENCH_PATH}/sites/{old_site_name}",
            f"{BENCH_PATH}/sites/{new_site_name}"
        ]

        shell_cmd = shlex.join(move_cmd)
        code, out, err = _run(shell_cmd)

        if code != 0:
            return False, f"Failed to move site directory: {err or out}"

        return True, f"Site renamed successfully from {old_site_name} to {new_site_name}"

    except Exception as e:
        frappe.log_error(f"Error renaming site: {str(e)}", "Site Rename Error")
        return False, f"Error renaming site: {str(e)}"


# ==================== API ENDPOINTS ====================

@frappe.whitelist()
@handle_exceptions
def update_site_domain(
    company_id: str,
    new_domain: str,
    user_password: str
) -> Dict[str, Any]:
    """
    Update the site domain (rename the site). Requires user password for security.

    Args:
        company_id: ID of the company
        new_domain: New domain/site name
        user_password: Current user's password for verification

    Returns:
        Dictionary with update status
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to update site domain")

    # Validate required fields
    if not new_domain or not new_domain.strip():
        return ResponseFormatter.validation_error(
            "New domain is required",
            {"new_domain": "Domain cannot be empty"}
        )

    if not user_password or not user_password.strip():
        return ResponseFormatter.validation_error(
            "User password is required",
            {"user_password": "Password cannot be empty"}
        )

    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permission
        if company_doc.customer_id != current_user and not frappe.has_permission("SaaS Company", "write", company_id):
            return ResponseFormatter.forbidden("You don't have permission to update this company")

        # Validate subscription
        from pix_one.api.companies.create_companies.create_companies_service import _validate_subscription

        is_valid, error_msg, _ = _validate_subscription(current_user, company_doc.subscription_id)
        if not is_valid:
            return ResponseFormatter.validation_error(
                f"Cannot update company: {error_msg}",
                {"subscription": "INVALID_OR_INACTIVE"}
            )

        # Only allow renaming for Active sites
        if company_doc.status != "Active":
            return ResponseFormatter.validation_error(
                f"Cannot rename site with status '{company_doc.status}'. Only Active sites can be renamed.",
                {"status": company_doc.status}
            )

        # Use domain field as it represents the actual site directory name
        old_site_name = company_doc.domain
        new_site_name = new_domain.lower().strip()

        # Check if new domain is the same as current
        if old_site_name == new_site_name:
            return ResponseFormatter.validation_error(
                "New domain is the same as current domain",
                {"new_domain": "Please provide a different domain"}
            )

        # Verify user password
        frappe.logger().info(f"Verifying password for user {current_user}")
        is_password_valid = _verify_user_password(current_user, user_password)

        if not is_password_valid:
            return ResponseFormatter.validation_error(
                "Invalid user password",
                {"user_password": "INVALID_PASSWORD"}
            )

        # Check if new site name already exists
        from pix_one.api.companies.create_companies.create_companies_service import _site_exists
        if _site_exists(new_site_name):
            return ResponseFormatter.validation_error(
                f"Site '{new_site_name}' already exists",
                {"new_domain": "SITE_EXISTS"}
            )

        # Update company status to indicate renaming in progress
        company_doc.db_set("site_status", "Renaming", update_modified=False)
        frappe.db.commit()

        # Rename the site
        success, message = _rename_site(old_site_name, new_site_name, company_doc)

        if not success:
            # Revert status on failure
            company_doc.db_set("site_status", "Active", update_modified=False)
            frappe.db.commit()

            return ResponseFormatter.server_error(
                f"Failed to rename site: {message}"
            )

        # Update company document with new site details
        company_doc.db_set("domain", new_domain, update_modified=False)
        company_doc.db_set("site_name", new_site_name, update_modified=False)
        company_doc.db_set("site_status", "Active", update_modified=False)
        company_doc.db_set("db_name", f"_{new_site_name}", update_modified=False)

        # Add note about the rename
        rename_note = f"Site renamed from {old_site_name} to {new_site_name} on {now_datetime()}"
        existing_notes = company_doc.provisioning_notes or ""
        new_notes = f"{existing_notes}\n{rename_note}" if existing_notes else rename_note
        company_doc.db_set("provisioning_notes", new_notes, update_modified=False)

        frappe.db.commit()

        # Reload to get fresh data
        company_doc.reload()

        return ResponseFormatter.updated(
            data={
                "company_id": company_doc.name,
                "company_name": company_doc.company_name,
                "old_site_name": old_site_name,
                "new_site_name": new_site_name,
                "site_url": company_doc.site_url,
                "status": company_doc.status,
                "site_status": company_doc.site_status
            },
            message=f"Site domain successfully updated from '{old_site_name}' to '{new_site_name}'"
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating site domain: {str(e)}", "Site Domain Update Error")
        return ResponseFormatter.server_error(f"Failed to update site domain: {str(e)}")
