import frappe
from frappe import _


def sync_customer_on_user_save(doc, method):
	"""
	Sync ERPNext Customer when a user is created or updated.
	This function is called after a User document is inserted or updated.

	Args:
		doc: The User document
		method: The event method (after_insert or on_update)
	"""

	# Only sync customer for Website Users (not System Users)
	if doc.user_type != "Website User":
		return

	try:
		# Check if customer already exists
		existing_customer = frappe.db.get_value(
			"Customer",
			{"email_id": doc.email},
			["name", "customer_name"],
			as_dict=True
		)

		if existing_customer:
			# Customer exists - update it
			_update_customer(doc, existing_customer.name)
		else:
			# Customer doesn't exist - create it
			_create_customer(doc)

	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title=f"Error syncing Customer for user {doc.email}"
		)
		# Don't raise the exception to avoid blocking user save
		frappe.logger().error(f"Failed to sync Customer for user {doc.email}: {str(e)}")


def _create_customer(user_doc):
	"""
	Create a new Customer from User data.

	Args:
		user_doc: The User document
	"""
	# Get default customer group and territory from settings
	customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual"
	territory = frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"

	# Create Customer document with user data
	customer = frappe.get_doc({
		"doctype": "Customer",
		"salutation": "Mr",
		"customer_name": user_doc.full_name + " - " + user_doc.email,
		"customer_type": "Individual",
		"customer_group": customer_group,
		"territory": territory,
		"email_id": user_doc.email,
		"first_name": user_doc.first_name,
		"last_name": user_doc.last_name,
		"mobile_no": user_doc.mobile_no if hasattr(user_doc, 'mobile_no') else None,
		"gender": user_doc.gender if hasattr(user_doc, 'gender') else None,
	})

	# Insert the customer document
	customer.insert(ignore_permissions=True)

	# Link the user to the customer as a portal user
	if not frappe.db.exists("Portal User", {"parent": customer.name, "user": user_doc.name}):
		customer.append("portal_users", {
			"user": user_doc.name
		})
		customer.save(ignore_permissions=True)

	frappe.db.commit()

	frappe.logger().info(f"Customer '{customer.name}' created successfully for user: {user_doc.email}")


def _update_customer(user_doc, customer_name):
	"""
	Update existing Customer with User data.

	Args:
		user_doc: The User document
		customer_name: Name of the existing Customer document
	"""
	customer = frappe.get_doc("Customer", customer_name)

	# Update customer fields with user data
	customer.customer_name = user_doc.full_name + " - " + user_doc.email
	customer.email_id = user_doc.email
	customer.first_name = user_doc.first_name
	customer.last_name = user_doc.last_name

	# Update optional fields if they exist
	if hasattr(user_doc, 'mobile_no') and user_doc.mobile_no:
		customer.mobile_no = user_doc.mobile_no

	if hasattr(user_doc, 'gender') and user_doc.gender:
		customer.gender = user_doc.gender

	# Ensure the user is linked as a portal user
	portal_user_exists = False
	for portal_user in customer.portal_users:
		if portal_user.user == user_doc.name:
			portal_user_exists = True
			break

	if not portal_user_exists:
		customer.append("portal_users", {
			"user": user_doc.name
		})

	customer.save(ignore_permissions=True)
	frappe.db.commit()

	frappe.logger().info(f"Customer '{customer.name}' updated successfully for user: {user_doc.email}")


# Keep backward compatibility - alias for after_insert hook
def create_customer_on_registration(doc, method):
	"""
	Legacy function name for backward compatibility.
	Calls the main sync function.
	"""
	sync_customer_on_user_save(doc, method)
