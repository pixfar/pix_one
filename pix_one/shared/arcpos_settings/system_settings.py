
import frappe


def default_system_settings():
    return frappe.get_single("PixOne System Settings")