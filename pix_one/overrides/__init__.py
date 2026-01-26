# Monkey-patching for Frappe core modules
# This file is imported from pix_one/__init__.py to apply overrides

import frappe.twofactor
from pix_one.overrides.twofactor import send_token_via_email

# Override 2FA email function
frappe.twofactor.send_token_via_email = send_token_via_email
