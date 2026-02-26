
# app information
app_name = "pix_one"
app_title = "Pix One"
app_publisher = "Pixfar"
app_description = "All in One ERP Solution"
app_email = "info@pixfar.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pix_one/css/pix_one.css"
# app_include_js = "/assets/pix_one/js/pix_one.js"

# include js, css files in header of web template
# web_include_css = "/assets/pix_one/css/pix_one.css"
# web_include_js = "/assets/pix_one/js/pix_one.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pix_one/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pix_one.utils.jinja_methods",
# 	"filters": "pix_one.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pix_one.install.before_install"
# after_install = "pix_one.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pix_one.uninstall.before_uninstall"
# after_uninstall = "pix_one.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pix_one.utils.before_app_install"
# after_app_install = "pix_one.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pix_one.utils.before_app_uninstall"
# after_app_uninstall = "pix_one.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pix_one.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Fixtures

fixtures = ["Print Format", "Custom Field", "Property Setter", "Client Script", "Server Script", "Workspace" ]

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"User": {
		"after_insert": "pix_one.utils.user_hooks.sync_customer_on_user_save",
		"on_update": "pix_one.utils.user_hooks.sync_customer_on_user_save"
	},
	"SaaS Subscription Plan": {
		"on_submit": "pix_one.utils.subscription_hooks.create_item_on_subscription_plan_submit"
	},
	"SaaS Company": {
		"after_insert": "pix_one.utils.company_hooks.update_subscription_on_company_change",
		"on_trash": "pix_one.utils.company_hooks.update_subscription_on_company_change"
	},
	"SaaS Subscriptions": {
		"on_update": [
			"pix_one.utils.company_hooks.validate_company_on_subscription_change",
			"pix_one.utils.company_hooks.auto_activate_companies_on_subscription_renewal"
		]
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"pix_one.tasks.subscription_scheduler.check_expired_subscriptions",
		"pix_one.tasks.subscription_scheduler.check_trial_expiry",
		"pix_one.tasks.subscription_scheduler.send_renewal_reminders",
		"pix_one.tasks.subscription_scheduler.process_auto_renewals",
		"pix_one.tasks.monitoring_jobs.take_usage_snapshots",
		"pix_one.tasks.monitoring_jobs.process_scheduled_downgrades",
		"pix_one.tasks.monitoring_jobs.cleanup_expired_invites",
	],
	"hourly": [
		"pix_one.tasks.subscription_scheduler.update_license_validation_status",
		"pix_one.tasks.monitoring_jobs.check_platform_health",
	],
	"weekly": [
		"pix_one.utils.jwt_auth.cleanup_expired_blacklist",
	]
}

# Testing
# -------

# before_tests = "pix_one.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "frappe.core.doctype.user.user.sign_up": "pix_one.overrides.user.sign_up",
    # Note: frappe.twofactor.send_token_via_email is NOT a whitelisted method,
    # so it's overridden via monkey-patching in pix_one/__init__.py instead
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pix_one.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pix_one.utils.before_request"]
# after_request = ["pix_one.utils.after_request"]

# Job Events
# ----------
# before_job = ["pix_one.utils.before_job"]
# after_job = ["pix_one.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

auth_hooks = [
	"pix_one.auth.validate"
]

website_route_rules = [
    {'from_route': '/pixone/<path:app_path>', 'to_route': 'dashboard'},
    {'from_route': '/pixone', 'to_route': 'dashboard'},
]

# Website context
update_website_context = "pix_one.www.dashboard.get_context"

