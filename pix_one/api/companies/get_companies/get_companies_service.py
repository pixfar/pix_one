"""
Company Retrieval Service for SaaS ERP Platform

This service provides comprehensive endpoints for listing and retrieving company information.
"""

from typing import Dict, Any, Optional

import frappe
from frappe import _
from frappe.utils import cstr

from pix_one.common.interceptors.response_interceptors import ResponseFormatter, handle_exceptions
from pix_one.common.shared.base_data_service import BaseDataService
from pix_one.common.shared.base_pagination import build_pagination_params


@frappe.whitelist()
@handle_exceptions
def get_companies(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    subscription_id: Optional[str] = None,
    sort_by: str = "creation",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """
    Get list of companies for the current user.

    Args:
        page: Page number (1-indexed)
        limit: Items per page
        search: Search query for company name or site name
        status: Filter by status (Active, Provisioning, Failed, etc.)
        subscription_id: Filter by subscription ID
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)

    Returns:
        Paginated list of companies
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to view companies")

    # Build filters
    filters = {"customer_id": current_user}

    if status:
        filters["status"] = status

    if subscription_id:
        filters["subscription_id"] = subscription_id

    # Build search fields
    search_fields = ["company_name", "site_name", "company_abbr"]

    # Get pagination params
    pagination = build_pagination_params(page, limit)

    try:
        # Get companies with pagination
        companies = BaseDataService.get_paginated_data(
            doctype="SaaS Company",
            pagination=pagination,
            filters=filters,
            search_query=search,
            search_fields=search_fields,
            order_by=f"{sort_by} {sort_order}"
        )

        # Format response
        company_list = []
        for company in companies["data"]:
            company_list.append({
                "company_id": company.name,
                "company_name": company.company_name,
                "company_abbr": company.company_abbr,
                "status": company.status,
                "site_name": company.site_name,
                "site_url": company.site_url,
                "site_status": company.site_status,
                "subscription_id": company.subscription_id,
                "erpnext_company_id": company.erpnext_company_id,
                "is_erpnext_synced": company.is_erpnext_synced,
                "created_at": cstr(company.creation),
                "provisioning_completed_at": cstr(company.provisioning_completed_at) if company.provisioning_completed_at else None
            })

        return ResponseFormatter.paginated(
            data=company_list,
            total=companies["total"],
            page=page,
            limit=limit,
            message=f"Found {companies['total']} companies"
        )

    except Exception as e:
        frappe.log_error(f"Error fetching companies: {str(e)}")
        return ResponseFormatter.server_error(f"Failed to fetch companies: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def get_company(company_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific company.

    Args:
        company_id: ID of the company

    Returns:
        Dictionary with complete company details
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to view company details")

    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permission
        if company_doc.customer_id != current_user and not frappe.has_permission("SaaS Company", "read", company_id):
            return ResponseFormatter.forbidden("You don't have permission to view this company")

        # Get subscription details if available
        subscription_info = None
        if company_doc.subscription_id:
            try:
                subscription = frappe.get_doc("SaaS Subscriptions", company_doc.subscription_id)
                plan = frappe.get_doc("SaaS Subscription Plan", subscription.plan_name)

                subscription_info = {
                    "subscription_id": subscription.name,
                    "subscription_status": subscription.status,
                    "plan_name": plan.plan_name,
                    "max_users": plan.max_users,
                    "max_storage_mb": plan.max_storage_mb,
                    "max_companies": plan.max_companies,
                    "billing_interval": subscription.billing_interval,
                    "next_billing_date": cstr(subscription.next_billing_date) if subscription.next_billing_date else None
                }
            except Exception as e:
                frappe.log_error(f"Error fetching subscription info: {str(e)}")

        # Build response
        company_data = {
            "company_id": company_doc.name,
            "company_name": company_doc.company_name,
            "company_abbr": company_doc.company_abbr,
            "status": company_doc.status,
            "site_name": company_doc.site_name,
            "site_url": company_doc.site_url,
            "site_status": company_doc.site_status,
            "admin_email": company_doc.admin_email,
            "default_currency": company_doc.default_currency,
            "country": company_doc.country,
            "domain": company_doc.domain,
            "erpnext_company_id": company_doc.erpnext_company_id,
            "is_erpnext_synced": company_doc.is_erpnext_synced,
            "db_name": company_doc.db_name,
            "db_host": company_doc.db_host,
            "db_port": company_doc.db_port,
            "is_dedicated_db": company_doc.is_dedicated_db,
            "provisioning_started_at": cstr(company_doc.provisioning_started_at) if company_doc.provisioning_started_at else None,
            "provisioning_completed_at": cstr(company_doc.provisioning_completed_at) if company_doc.provisioning_completed_at else None,
            "last_accessed_at": cstr(company_doc.last_accessed_at) if company_doc.last_accessed_at else None,
            "provisioning_notes": company_doc.provisioning_notes,
            "created_at": cstr(company_doc.creation),
            "created_by": company_doc.created_by_user,
            "subscription": subscription_info
        }

        # Update last accessed timestamp
        company_doc.db_set("last_accessed_at", frappe.utils.now_datetime(), update_modified=False)
        frappe.db.commit()

        return ResponseFormatter.success(
            data=company_data,
            message=f"Company details retrieved successfully"
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        frappe.log_error(f"Error fetching company: {str(e)}")
        return ResponseFormatter.server_error(f"Failed to fetch company details: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def get_company_stats() -> Dict[str, Any]:
    """
    Get aggregated statistics for the current user's companies.

    Returns:
        Dictionary with company statistics
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to view statistics")

    try:
        # Count by status
        total_companies = frappe.db.count("SaaS Company", {
            "customer_id": current_user,
            "status": ["not in", ["Deleted"]]
        })

        active_companies = frappe.db.count("SaaS Company", {
            "customer_id": current_user,
            "status": "Active"
        })

        provisioning_companies = frappe.db.count("SaaS Company", {
            "customer_id": current_user,
            "status": "Provisioning"
        })

        failed_companies = frappe.db.count("SaaS Company", {
            "customer_id": current_user,
            "status": "Failed"
        })

        suspended_companies = frappe.db.count("SaaS Company", {
            "customer_id": current_user,
            "status": "Suspended"
        })

        # Get subscription info
        subscription = frappe.db.get_value(
            "SaaS Subscriptions",
            {
                "customer_id": current_user,
                "status": "Active"
            },
            ["name", "plan_name"],
            as_dict=True,
            order_by="creation desc"
        )

        quota_info = None
        if subscription:
            plan = frappe.get_doc("SaaS Subscription Plan", subscription.plan_name)
            quota_info = {
                "max_companies": plan.max_companies,
                "used_companies": active_companies + provisioning_companies,
                "available_companies": max(0, plan.max_companies - active_companies - provisioning_companies),
                "percentage_used": round((active_companies + provisioning_companies) / plan.max_companies * 100, 2) if plan.max_companies > 0 else 0
            }

        stats = {
            "total_companies": total_companies,
            "active_companies": active_companies,
            "provisioning_companies": provisioning_companies,
            "failed_companies": failed_companies,
            "suspended_companies": suspended_companies,
            "quota": quota_info
        }

        return ResponseFormatter.success(
            data=stats,
            message="Statistics retrieved successfully"
        )

    except Exception as e:
        frappe.log_error(f"Error fetching stats: {str(e)}")
        return ResponseFormatter.server_error(f"Failed to fetch statistics: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def update_company(
    company_id: str,
    company_name: Optional[str] = None,
    admin_email: Optional[str] = None,
    default_currency: Optional[str] = None,
    country: Optional[str] = None,
    domain: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update company details.

    Args:
        company_id: ID of the company to update
        company_name: New company name (optional)
        admin_email: New admin email (optional)
        default_currency: New default currency (optional)
        country: New country (optional)
        domain: New domain (optional)

    Returns:
        Dictionary with updated company details
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to update company")

    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permission
        if company_doc.customer_id != current_user and not frappe.has_permission("SaaS Company", "write", company_id):
            return ResponseFormatter.forbidden("You don't have permission to update this company")

        # Validate subscription when updating
        from pix_one.api.companies.create_companies.create_companies_service import _validate_subscription

        is_valid, error_msg, _ = _validate_subscription(current_user, company_doc.subscription_id)
        if not is_valid:
            return ResponseFormatter.validation_error(
                f"Cannot update company: {error_msg}",
                {"subscription": "INVALID_OR_INACTIVE"}
            )

        # Update fields
        if company_name:
            company_doc.company_name = company_name

        if admin_email:
            company_doc.admin_email = admin_email

        if default_currency:
            company_doc.default_currency = default_currency

        if country:
            company_doc.country = country

        if domain:
            company_doc.domain = domain

        company_doc.save(ignore_permissions=True)
        frappe.db.commit()

        return ResponseFormatter.updated(
            data={
                "company_id": company_doc.name,
                "company_name": company_doc.company_name,
                "admin_email": company_doc.admin_email,
                "default_currency": company_doc.default_currency,
                "country": company_doc.country,
                "domain": company_doc.domain
            },
            message="Company updated successfully"
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error updating company: {str(e)}")
        return ResponseFormatter.server_error(f"Failed to update company: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def suspend_company(company_id: str) -> Dict[str, Any]:
    """
    Suspend a company (makes it inaccessible but doesn't delete it).

    Args:
        company_id: ID of the company to suspend

    Returns:
        Dictionary with suspension status
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to suspend company")

    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permission
        if company_doc.customer_id != current_user and not frappe.has_permission("SaaS Company", "write", company_id):
            return ResponseFormatter.forbidden("You don't have permission to suspend this company")

        if company_doc.status == "Suspended":
            return ResponseFormatter.validation_error(
                "Company is already suspended",
                {"status": company_doc.status}
            )

        company_doc.db_set("status", "Suspended", update_modified=True)
        frappe.db.commit()

        return ResponseFormatter.success(
            data={"company_id": company_id, "status": "Suspended"},
            message=f"Company '{company_doc.company_name}' has been suspended"
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        frappe.db.rollback()
        return ResponseFormatter.server_error(f"Failed to suspend company: {str(e)}")


@frappe.whitelist()
@handle_exceptions
def activate_company(company_id: str) -> Dict[str, Any]:
    """
    Activate a suspended company.

    Args:
        company_id: ID of the company to activate

    Returns:
        Dictionary with activation status
    """
    current_user = frappe.session.user

    if current_user == "Guest":
        return ResponseFormatter.unauthorized("Please login to activate company")

    try:
        company_doc = frappe.get_doc("SaaS Company", company_id)

        # Check permission
        if company_doc.customer_id != current_user and not frappe.has_permission("SaaS Company", "write", company_id):
            return ResponseFormatter.forbidden("You don't have permission to activate this company")

        if company_doc.status != "Suspended":
            return ResponseFormatter.validation_error(
                "Only suspended companies can be activated",
                {"status": company_doc.status}
            )

        company_doc.db_set("status", "Active", update_modified=True)
        frappe.db.commit()

        return ResponseFormatter.success(
            data={"company_id": company_id, "status": "Active"},
            message=f"Company '{company_doc.company_name}' has been activated"
        )

    except frappe.DoesNotExistError:
        return ResponseFormatter.not_found(f"Company {company_id} not found")
    except Exception as e:
        frappe.db.rollback()
        return ResponseFormatter.server_error(f"Failed to activate company: {str(e)}")
