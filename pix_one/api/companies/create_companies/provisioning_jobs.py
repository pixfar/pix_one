"""
Background job functions for company site provisioning.
These functions run asynchronously to avoid blocking API responses.
"""

import os
import json
from typing import Dict, Any

import frappe
from frappe.utils import now_datetime

from pix_one.api.companies.create_companies.create_companies_service import (
    _get_db_config,
    _provision_frappe_site,
    _install_apps_on_site,
    BENCH_PATH
)


def provision_company_site(
    company_id: str,
    site_name: str,
    admin_password: str,
    admin_email: str,
    customer_email: str,
    apps_to_install: list = None
):
    """
    Background job to provision a company site.

    Args:
        company_id: SaaS Company document ID
        site_name: Name of the site to create
        admin_password: Admin password for the site
        admin_email: Admin email for the site (site administrator)
        customer_email: Customer's email (where notification will be sent)
        apps_to_install: List of apps to install
    """
    try:
        # Get the company document
        company_doc = frappe.get_doc("SaaS Company", company_id)

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

        # Update completion status
        company_doc.db_set("status", "Active", update_modified=False)
        company_doc.db_set("provisioning_completed_at", now_datetime(), update_modified=False)
        company_doc.db_set("provisioning_notes", "\n".join(provisioning_notes), update_modified=False)
        frappe.db.commit()

        # Reload document
        company_doc.reload()

        # Send success email to customer
        send_provisioning_complete_email(
            company_doc=company_doc,
            customer_email=customer_email,
            admin_email=admin_email,
            admin_password=admin_password,
            success=True
        )

        frappe.logger().info(f"Successfully provisioned site {site_name} for company {company_id}")

    except Exception as e:
        # Mark as failed
        try:
            company_doc = frappe.get_doc("SaaS Company", company_id)
            company_doc.db_set("status", "Failed", update_modified=False)
            company_doc.db_set("provisioning_notes", f"Error: {str(e)}", update_modified=False)
            frappe.db.commit()

            # Send failure email to customer
            send_provisioning_complete_email(
                company_doc=company_doc,
                customer_email=customer_email,
                admin_email=admin_email,
                admin_password=None,
                success=False,
                error_message=str(e)
            )
        except Exception as email_error:
            frappe.log_error(f"Failed to send error email: {str(email_error)}", "Provisioning Email Error")

        frappe.log_error(f"Company site provisioning failed: {str(e)}", "Company Provisioning Error")
        raise


def send_provisioning_complete_email(
    company_doc,
    customer_email: str,
    admin_email: str,
    admin_password: str = None,
    success: bool = True,
    error_message: str = None
):
    """
    Send email notification when provisioning is complete.

    Args:
        company_doc: SaaS Company document
        customer_email: Customer's email address (where notification will be sent)
        admin_email: Admin email for the site (site administrator login)
        admin_password: Admin password (only sent on success)
        success: Whether provisioning was successful
        error_message: Error message if failed
    """
    try:
        if success:
            subject = f"Your Site is Ready: {company_doc.company_name}"
            message = f"""
<h2>Your Site Has Been Successfully Provisioned!</h2>

<p>Dear Customer,</p>

<p>Great news! Your new site for <strong>{company_doc.company_name}</strong> is now ready to use.</p>

<h3>Site Details:</h3>
<ul>
    <li><strong>Company Name:</strong> {company_doc.company_name}</li>
    <li><strong>Site URL:</strong> <a href="{company_doc.site_url}">{company_doc.site_url}</a></li>
    <li><strong>Admin Email:</strong> {admin_email}</li>
    <li><strong>Admin Password:</strong> {admin_password}</li>
</ul>

<h3>Next Steps:</h3>
<ol>
    <li>Visit your site at <a href="{company_doc.site_url}">{company_doc.site_url}</a></li>
    <li>Log in using the credentials above</li>
    <li>Change your password after first login</li>
    <li>Start setting up your workspace</li>
</ol>

<p><strong>Important:</strong> Please save your credentials securely. For security reasons, we won't be able to send this password again.</p>

<p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>

<p>Best regards,<br>
The PIX One Team</p>
            """
        else:
            subject = f"Site Provisioning Failed: {company_doc.company_name}"
            message = f"""
<h2>Site Provisioning Failed</h2>

<p>Dear Customer,</p>

<p>We encountered an issue while setting up your site for <strong>{company_doc.company_name}</strong>.</p>

<h3>Error Details:</h3>
<p><code>{error_message}</code></p>

<p>Our team has been notified and will investigate this issue. We'll reach out to you shortly to resolve this.</p>

<p>If you need immediate assistance, please contact our support team with reference ID: <strong>{company_doc.name}</strong></p>

<p>We apologize for the inconvenience.</p>

<p>Best regards,<br>
The PIX One Team</p>
            """

        # Send email using Frappe's email API
        frappe.sendmail(
            recipients=[customer_email],
            subject=subject,
            message=message,
            now=True  # Send immediately
        )

        frappe.logger().info(f"Provisioning email sent to {customer_email} for company {company_doc.name}")

    except Exception as e:
        frappe.log_error(
            f"Failed to send provisioning email to {customer_email}: {str(e)}",
            "Provisioning Email Error"
        )
