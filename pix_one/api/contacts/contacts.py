import frappe
from pix_one.common.shared.base_data_service import BaseDataService

@frappe.whitelist()
def get_my_contacts():
    """
    Retrieve session users contacts with their addresses
    """
    return BaseDataService.get_current_user()