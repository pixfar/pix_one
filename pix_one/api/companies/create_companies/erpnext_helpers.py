"""
Helper functions for ERPNext company creation.
These functions are designed to be called via bench execute.
"""

import frappe


def create_erpnext_company(company_name, company_abbr, default_currency="USD", country="United States"):
    """
    Create an ERPNext company.

    This function is designed to be called via bench execute command.

    Args:
        company_name: Company name
        company_abbr: Company abbreviation
        default_currency: Default currency code
        country: Country name

    Returns:
        Company name (ID)
    """
    company_doc = frappe.get_doc({
        "doctype": "Company",
        "company_name": company_name,
        "abbr": company_abbr,
        "default_currency": default_currency,
        "country": country
    })
    company_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    # Return just the company name
    return company_doc.name
