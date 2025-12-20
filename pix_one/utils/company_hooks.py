"""
Company Hooks for SaaS ERP Platform

This module provides hooks for the SaaS Company doctype to ensure proper
integration with subscriptions and license validation.
"""

import frappe
from frappe import _


def update_subscription_on_company_change(doc, method):
    """
    Update subscription when a company is created or deleted.
    This hook is called on after_insert and on_trash events.

    Args:
        doc: SaaS Company document
        method: Event method name
    """
    try:
        if not doc.subscription_id:
            return

        # Count active companies for this subscription
        company_count = frappe.db.count("SaaS Company", {
            "subscription_id": doc.subscription_id,
            "status": ["not in", ["Deleted", "Failed"]]
        })

        # Update subscription
        frappe.db.set_value(
            "SaaS Subscriptions",
            doc.subscription_id,
            "current_companies",
            company_count,
            update_modified=False
        )

        # Update license validation
        update_license_company_count(doc.subscription_id, company_count)

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(
            f"Error updating subscription on company change: {str(e)}",
            "Company Hook Error"
        )


def update_license_company_count(subscription_id, count):
    """
    Update company count in license validation record.

    Args:
        subscription_id: Subscription ID
        count: New company count
    """
    try:
        license_name = frappe.db.get_value(
            "SaaS App Validation",
            {"subscription_id": subscription_id},
            "name"
        )

        if license_name:
            frappe.db.set_value(
                "SaaS App Validation",
                license_name,
                "current_companies",
                count,
                update_modified=False
            )

    except Exception as e:
        frappe.log_error(
            f"Error updating license company count: {str(e)}",
            "License Update Error"
        )


def validate_company_on_subscription_change(doc, method):
    """
    Validate companies when subscription is downgraded or cancelled.
    This hook is called on SaaS Subscriptions on_update event.

    Args:
        doc: SaaS Subscriptions document
        method: Event method name
    """
    try:
        # Check if subscription status changed to non-active
        if doc.has_value_changed("status") and doc.status not in ["Active", "Trial"]:
            # Suspend all companies under this subscription
            companies = frappe.get_all(
                "SaaS Company",
                filters={
                    "subscription_id": doc.name,
                    "status": ["in", ["Active", "Provisioning"]]
                },
                fields=["name", "company_name"]
            )

            for company in companies:
                frappe.db.set_value(
                    "SaaS Company",
                    company.name,
                    "status",
                    "Suspended",
                    update_modified=True
                )

                frappe.logger().info(
                    f"Suspended company {company.company_name} due to subscription status: {doc.status}"
                )

            if companies:
                frappe.msgprint(
                    f"Suspended {len(companies)} companies due to subscription status change",
                    indicator="orange",
                    alert=True
                )

        # Check if plan changed (downgrade scenario)
        if doc.has_value_changed("plan_name"):
            validate_companies_against_new_plan(doc)

    except Exception as e:
        frappe.log_error(
            f"Error validating companies on subscription change: {str(e)}",
            "Subscription Hook Error"
        )


def validate_companies_against_new_plan(subscription_doc):
    """
    Validate that company count doesn't exceed new plan limits.

    Args:
        subscription_doc: SaaS Subscriptions document
    """
    try:
        plan = frappe.get_doc("SaaS Subscription Plan", subscription_doc.plan_name)
        max_companies = plan.max_companies or 1

        # Count active companies
        company_count = frappe.db.count("SaaS Company", {
            "subscription_id": subscription_doc.name,
            "status": ["not in", ["Deleted", "Failed", "Suspended"]]
        })

        if company_count > max_companies:
            # Suspend excess companies (keep oldest ones active)
            companies = frappe.get_all(
                "SaaS Company",
                filters={
                    "subscription_id": subscription_doc.name,
                    "status": ["in", ["Active", "Provisioning"]]
                },
                fields=["name", "company_name"],
                order_by="creation asc"
            )

            # Keep first max_companies, suspend the rest
            for idx, company in enumerate(companies):
                if idx >= max_companies:
                    frappe.db.set_value(
                        "SaaS Company",
                        company.name,
                        "status",
                        "Suspended",
                        update_modified=True
                    )

                    frappe.logger().warning(
                        f"Suspended company {company.company_name} due to plan downgrade"
                    )

            suspended_count = len(companies) - max_companies
            frappe.msgprint(
                f"Plan allows {max_companies} companies. Suspended {suspended_count} excess companies.",
                indicator="orange",
                alert=True
            )

    except Exception as e:
        frappe.log_error(
            f"Error validating companies against new plan: {str(e)}",
            "Plan Validation Error"
        )


def auto_activate_companies_on_subscription_renewal(doc, method):
    """
    Auto-activate suspended companies when subscription is renewed.

    Args:
        doc: SaaS Subscriptions document
        method: Event method name
    """
    try:
        # Check if status changed from Past Due/Expired to Active
        if (doc.has_value_changed("status") and
            doc.status == "Active" and
            doc.get_doc_before_save() and
            doc.get_doc_before_save().status in ["Past Due", "Expired"]):

            # Reactivate suspended companies (respecting quota)
            plan = frappe.get_doc("SaaS Subscription Plan", doc.plan_name)
            max_companies = plan.max_companies or 1

            suspended_companies = frappe.get_all(
                "SaaS Company",
                filters={
                    "subscription_id": doc.name,
                    "status": "Suspended"
                },
                fields=["name", "company_name"],
                order_by="creation asc",
                limit=max_companies
            )

            for company in suspended_companies:
                frappe.db.set_value(
                    "SaaS Company",
                    company.name,
                    "status",
                    "Active",
                    update_modified=True
                )

                frappe.logger().info(
                    f"Reactivated company {company.company_name} after subscription renewal"
                )

            if suspended_companies:
                frappe.msgprint(
                    f"Reactivated {len(suspended_companies)} companies after subscription renewal",
                    indicator="green",
                    alert=True
                )

    except Exception as e:
        frappe.log_error(
            f"Error auto-activating companies: {str(e)}",
            "Auto-Activation Error"
        )
