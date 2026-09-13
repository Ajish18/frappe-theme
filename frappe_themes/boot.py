# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe


def extend_bootinfo(bootinfo):
	"""Attach the active theme to the desk boot payload.

	Kept deliberately defensive: a theme is cosmetic, and nothing here is worth
	taking the desk down for. If resolution fails the desk boots unthemed.
	"""
	try:
		from frappe_themes.api import get_boot_info

		bootinfo.frappe_themes = get_boot_info()
	except Exception:
		frappe.log_error("Failed to load theme", frappe.get_traceback())
		bootinfo.frappe_themes = {"slug": None, "css": "", "allow_user_override": 1}
