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
from pix_one.common.shared.base_pagination import get_pagination_params


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
    additional_filters = {"customer_id": current_user}

    if status:
        additional_filters["status"] = status

    if subscription_id:
        additional_filters["subscription_id"] = subscription_id

    # Build search fields
    search_fields = ["company_name", "site_name", "company_abbr"]

    # Get pagination params
    pagination = get_pagination_params(
        page=page,
        limit=limit,
        sort=sort_by,
        order=sort_order,
        search=search,
        fields="*"
    )

    try:
        # Get companies with pagination
        data, total_count = BaseDataService.get_paginated_data(
            doctype="SaaS Company",
            pagination=pagination,
            additional_filters=additional_filters,
            search_fields=search_fields
        )

        # Format response
        company_list = []
        for company in data:
            company_list.append({
                "company_id": company.name,
                "company_name": company.company_name,
                "company_abbr": company.company_abbr,
                "status": company.status,
                "site_name": company.site_name,
                "site_url": company.site_url,
                "site_status": company.site_status,
                "subscription_id": company.subscription_id,
                "erpnext_company_id": company.get("erpnext_company_id"),
                "is_erpnext_synced": company.get("is_erpnext_synced"),
                "created_at": cstr(company.creation),
                "provisioning_completed_at": cstr(company.provisioning_completed_at) if company.get("provisioning_completed_at") else None
            })

        return ResponseFormatter.paginated(
            data=company_list,
            total=total_count,
            page=page,
            limit=limit,
            message=f"Found {total_count} companies"
        )

    except Exception as e:
        frappe.log_error(f"Error fetching companies: {str(e)}")
        return ResponseFormatter.server_error(f"Failed to fetch companies: {str(e)}")

