"""
Background jobs for site backup and restore operations.
"""

import os
import shlex
import subprocess

import frappe
from frappe import _
from frappe.utils import now_datetime


BENCH_PATH = os.getenv("BENCH_PATH", "/workspace/development/frappe-bench")


def _run_bench(cmd_list, timeout=600):
	if not os.path.isdir(BENCH_PATH):
		return 1, "", f"Bench path not found: {BENCH_PATH}"
	shell_cmd = f"cd {shlex.quote(BENCH_PATH)} && {shlex.join(cmd_list)}"
	res = subprocess.run(["bash", "-lc", shell_cmd], capture_output=True, text=True, timeout=timeout)
	return res.returncode, res.stdout, res.stderr


def run_backup(company_id, site_name):
	"""Background job: Run a site backup and record it."""
	backup_doc = None
	try:
		# Create backup record
		backup_doc = frappe.get_doc({
			"doctype": "SaaS Site Backup",
			"company_id": company_id,
			"backup_type": "Full",
			"status": "In Progress",
		})
		backup_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		# Run bench backup
		code, out, err = _run_bench(
			["bench", "--site", site_name, "backup", "--with-files"],
			timeout=600
		)

		if code != 0:
			backup_doc.db_set("status", "Failed")
			frappe.log_error(f"Backup failed for {site_name}: {err}", "Site Backup Error")
			frappe.db.commit()
			return

		# Parse backup output for file path
		file_url = None
		file_size_mb = 0
		for line in out.strip().splitlines():
			if "database backup" in line.lower() or line.strip().endswith(".sql.gz"):
				file_url = line.strip()
				break

		# Try to get file size
		if file_url and os.path.exists(file_url):
			file_size_mb = round(os.path.getsize(file_url) / (1024 * 1024), 2)

		backup_doc.db_set("status", "Completed")
		backup_doc.db_set("file_url", file_url or "")
		backup_doc.db_set("file_size_mb", file_size_mb)
		frappe.db.commit()

		# Notify user
		company = frappe.get_doc("SaaS Company", company_id)
		if company.customer_id:
			try:
				frappe.get_doc({
					"doctype": "Notification Log",
					"for_user": company.customer_id,
					"from_user": "Administrator",
					"subject": _("Backup completed for {0}").format(company.company_name),
					"email_content": _("Your site backup has been completed successfully."),
					"document_type": "SaaS Site Backup",
					"document_name": backup_doc.name,
					"type": "Alert",
					"read": 0
				}).insert(ignore_permissions=True)
				frappe.db.commit()
			except Exception:
				pass

	except Exception as e:
		if backup_doc:
			backup_doc.db_set("status", "Failed")
			frappe.db.commit()
		frappe.log_error(frappe.get_traceback(), "Site Backup Error")


def run_restore(company_id, backup_id):
	"""Background job: Restore a site from backup."""
	try:
		backup = frappe.get_doc("SaaS Site Backup", backup_id)
		company = frappe.get_doc("SaaS Company", company_id)

		if not backup.file_url:
			frappe.log_error(f"No backup file URL for {backup_id}", "Site Restore Error")
			return

		if not company.site_name:
			frappe.log_error(f"No site name for company {company_id}", "Site Restore Error")
			return

		# Run restore
		code, out, err = _run_bench(
			["bench", "--site", company.site_name, "restore", backup.file_url],
			timeout=600
		)

		if code != 0:
			frappe.log_error(f"Restore failed for {company.site_name}: {err}", "Site Restore Error")
			# Notify user of failure
			_notify_user(company.customer_id, company.company_name, success=False)
			return

		# Run migrate after restore
		_run_bench(["bench", "--site", company.site_name, "migrate"], timeout=600)

		# Notify user of success
		_notify_user(company.customer_id, company.company_name, success=True)

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Site Restore Error")


def _notify_user(user, company_name, success=True):
	"""Send notification about restore status."""
	if not user:
		return
	try:
		subject = (
			_("Restore completed for {0}").format(company_name)
			if success
			else _("Restore failed for {0}").format(company_name)
		)
		message = (
			_("Your site has been restored successfully.")
			if success
			else _("Site restore failed. Please contact support.")
		)
		frappe.get_doc({
			"doctype": "Notification Log",
			"for_user": user,
			"from_user": "Administrator",
			"subject": subject,
			"email_content": message,
			"type": "Alert",
			"read": 0
		}).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		pass
