# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe_themes.api import clear_theme_cache


class FrappeTheme(Document):
	def validate(self):
		self.set_slug()
		self.validate_chroma()

	def set_slug(self):
		if not self.slug:
			self.slug = frappe.scrub(self.theme_name).replace("_", "-")

	def validate_chroma(self):
		if self.neutral_chroma is None:
			self.neutral_chroma = 0.05
		if not 0 <= self.neutral_chroma <= 1:
			frappe.throw(_("Neutral Chroma must be between 0 and 1."))

	def on_update(self):
		clear_theme_cache(self.name)

	def on_trash(self):
		if self.is_standard and not frappe.flags.in_migrate and not frappe.flags.in_uninstall:
			frappe.throw(_("Standard themes cannot be deleted. Disable it instead."))

		if frappe.db.exists("User", {"frappe_theme": self.name}):
			frappe.db.set_value("User", {"frappe_theme": self.name}, "frappe_theme", None)

	def after_delete(self):
		clear_theme_cache(self.name)

	def as_spec(self) -> dict:
		"""The plain dict the colour engine works with."""
		return {
			"slug": self.slug,
			"theme_name": self.theme_name,
			"description": self.description,
			"mode": self.mode,
			"accent": self.accent,
			"neutral_tint": self.neutral_tint,
			"neutral_chroma": self.neutral_chroma,
			"sidebar_style": self.sidebar_style,
			"sidebar_bg": self.sidebar_bg,
			"custom_css": self.custom_css,
		}


def get_enabled_specs() -> list:
	"""Specs for every enabled theme, standard ones first."""
	names = frappe.get_all(
		"Frappe Theme",
		filters={"enabled": 1},
		order_by="is_standard desc, mode asc, theme_name asc",
		pluck="name",
	)
	specs = []
	for name in names:
		doc = frappe.get_cached_doc("Frappe Theme", name)
		if doc.slug:
			specs.append(doc.as_spec())
	return specs
