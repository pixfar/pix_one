import frappe
from frappe import _


def create_item_on_subscription_plan_submit(doc, method):
	"""
	Create an ERPNext Item when a SaaS Subscription Plan is submitted.
	This function is called on_submit event.

	Args:
		doc: The SaaS Subscription Plan document
		method: The event method (on_submit)
	"""

	try:
		# Check if item already exists for this subscription plan
		existing_item = frappe.db.exists("Item", {"item_code": doc.plan_code})
		if existing_item:
			frappe.logger().info(f"Item already exists for subscription plan: {doc.plan_code}")
			# Update the existing item instead
			_update_item_from_plan(doc, existing_item)
			return

		# Create new item
		_create_item_from_plan(doc)

	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title=f"Error creating Item for SaaS Subscription Plan {doc.name}"
		)
		# Don't raise the exception to avoid blocking plan submission
		frappe.logger().error(f"Failed to create Item for plan {doc.name}: {str(e)}")


def _create_item_from_plan(plan_doc):
	"""
	Create a new Item from SaaS Subscription Plan data.

	Args:
		plan_doc: The SaaS Subscription Plan document
	"""

	# Get default item group for services/subscriptions
	item_group = frappe.db.get_single_value("Stock Settings", "item_group") or "Products"

	# Build item description with plan details
	description = f"<p>{plan_doc.short_description or plan_doc.plan_name}</p>"
	description += f"<p><strong>Billing Interval:</strong> {plan_doc.billing_interval}</p>"

	if plan_doc.max_users:
		description += f"<p><strong>Max Users:</strong> {plan_doc.max_users}</p>"
	if plan_doc.max_storage_mb:
		description += f"<p><strong>Max Storage:</strong> {plan_doc.max_storage_mb} MB</p>"
	if plan_doc.max_companies:
		description += f"<p><strong>Max Companies:</strong> {plan_doc.max_companies}</p>"

	# Create Item document
	item = frappe.get_doc({
		"doctype": "Item",
		"item_code": plan_doc.plan_code,
		"item_name": plan_doc.plan_name,
		"item_group": item_group,
		"stock_uom": "Nos",
		"is_stock_item": 0,  # Service item, not a stock item
		"is_sales_item": 1,  # Can be sold
		"is_purchase_item": 0,  # Not purchased
		"description": description,
		"standard_rate": plan_doc.price,
		"disabled": 0 if plan_doc.is_active else 1,
	})

	# Add item defaults with the plan's currency
	if plan_doc.currency:
		item.append("item_defaults", {
			"company": frappe.defaults.get_defaults().get("company"),
			"default_price_list": frappe.db.get_single_value("Selling Settings", "selling_price_list"),
		})

	# Insert the item
	item.insert(ignore_permissions=True)

	# Create an Item Price record
	_create_item_price(plan_doc, item.name)

	frappe.db.commit()

	frappe.logger().info(f"Item '{item.name}' created successfully for subscription plan: {plan_doc.name}")


def _update_item_from_plan(plan_doc, item_code):
	"""
	Update existing Item with SaaS Subscription Plan data.

	Args:
		plan_doc: The SaaS Subscription Plan document
		item_code: Item code of the existing Item
	"""

	item = frappe.get_doc("Item", item_code)

	# Update item fields
	item.item_name = plan_doc.plan_name
	item.standard_rate = plan_doc.price
	item.disabled = 0 if plan_doc.is_active else 1

	# Update description
	description = f"<p>{plan_doc.short_description or plan_doc.plan_name}</p>"
	description += f"<p><strong>Billing Interval:</strong> {plan_doc.billing_interval}</p>"

	if plan_doc.max_users:
		description += f"<p><strong>Max Users:</strong> {plan_doc.max_users}</p>"
	if plan_doc.max_storage_mb:
		description += f"<p><strong>Max Storage:</strong> {plan_doc.max_storage_mb} MB</p>"
	if plan_doc.max_companies:
		description += f"<p><strong>Max Companies:</strong> {plan_doc.max_companies}</p>"

	item.description = description

	item.save(ignore_permissions=True)

	# Update Item Price
	_create_or_update_item_price(plan_doc, item.name)

	frappe.db.commit()

	frappe.logger().info(f"Item '{item.name}' updated successfully for subscription plan: {plan_doc.name}")


def _create_item_price(plan_doc, item_code):
	"""
	Create an Item Price record for the subscription plan item.

	Args:
		plan_doc: The SaaS Subscription Plan document
		item_code: Item code of the created Item
	"""

	# Get default price list
	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"

	# Check if item price already exists
	existing_price = frappe.db.exists("Item Price", {
		"item_code": item_code,
		"price_list": price_list
	})

	if existing_price:
		return

	# Create item price
	item_price = frappe.get_doc({
		"doctype": "Item Price",
		"item_code": item_code,
		"price_list": price_list,
		"currency": plan_doc.currency,
		"price_list_rate": plan_doc.price,
	})

	item_price.insert(ignore_permissions=True)

	frappe.logger().info(f"Item Price created for item '{item_code}' in price list '{price_list}'")


def _create_or_update_item_price(plan_doc, item_code):
	"""
	Create or update Item Price record for the subscription plan item.

	Args:
		plan_doc: The SaaS Subscription Plan document
		item_code: Item code of the Item
	"""

	# Get default price list
	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list") or "Standard Selling"

	# Check if item price already exists
	existing_price = frappe.db.get_value("Item Price", {
		"item_code": item_code,
		"price_list": price_list
	}, "name")

	if existing_price:
		# Update existing price
		item_price = frappe.get_doc("Item Price", existing_price)
		item_price.currency = plan_doc.currency
		item_price.price_list_rate = plan_doc.price
		item_price.save(ignore_permissions=True)
		frappe.logger().info(f"Item Price updated for item '{item_code}'")
	else:
		# Create new price
		_create_item_price(plan_doc, item_code)
