# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe


def extend_bootinfo(bootinfo):
	"""Attach the active theme's CSS to the desk boot payload.

	Kept deliberately defensive: a theme is cosmetic, and nothing here is worth
	taking the desk down for. If anything goes wrong the desk boots unthemed
	rather than failing the request.
	"""
	try:
		from frappe_themes.api import get_boot_info

		bootinfo.frappe_themes = get_boot_info()
	except Exception:
		frappe.log_error("frappe_themes: failed to build boot payload", frappe.get_traceback())
		bootinfo.frappe_themes = {"active": False, "css": ""}
