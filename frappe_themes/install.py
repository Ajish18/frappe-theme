# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from frappe_themes.standard_themes import STANDARD_THEMES

# The per-user selection. A custom field on User rather than a doctype of our own
# keeps it on the record the desk already loads and caches for every request.
USER_FIELDS = {
	"User": [
		{
			"fieldname": "frappe_theme",
			"label": "Theme",
			"fieldtype": "Link",
			"options": "Frappe Theme",
			"insert_after": "desk_theme",
			"description": "Colour theme for the desk. Set from the theme switcher.",
		}
	]
}


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	create_custom_fields(USER_FIELDS, ignore_validate=True)
	install_standard_themes()
	set_default_theme()

	from frappe_themes.api import clear_theme_cache

	clear_theme_cache()


def install_standard_themes():
	"""Insert or refresh the shipped themes.

	Standard themes are owned by the app: they are rewritten on every migrate so
	an upgrade can correct a palette. Anything a user creates is left alone, and
	the intended way to tweak a shipped theme is to duplicate it.
	"""
	for spec in STANDARD_THEMES:
		values = dict(spec, is_standard=1, enabled=1)
		name = spec["theme_name"]

		if frappe.db.exists("Frappe Theme", name):
			doc = frappe.get_doc("Frappe Theme", name)
			doc.update(values)
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc({"doctype": "Frappe Theme", **values})
			doc.insert(ignore_permissions=True)


def set_default_theme():
	settings = frappe.get_single("Frappe Theme Settings")
	if not settings.default_theme and frappe.db.exists("Frappe Theme", "Emerald Light"):
		settings.default_theme = "Emerald Light"
		settings.save(ignore_permissions=True)


def before_uninstall():
	"""Take the custom field with us so User stops pointing at a missing doctype."""
	frappe.flags.in_uninstall = True
	if frappe.db.exists("Custom Field", "User-frappe_theme"):
		frappe.delete_doc("Custom Field", "User-frappe_theme", ignore_permissions=True, force=True)
