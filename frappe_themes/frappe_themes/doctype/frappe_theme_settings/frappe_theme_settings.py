# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FrappeThemeSettings(Document):
	def on_update(self):
		# The resolved theme is cached per user and the default feeds into it.
		frappe.cache.delete_value("frappe_themes_catalogue")
		frappe.clear_cache()
