# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

HEX_RE = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")

COLOR_FIELDS = (
	"sidebar_background",
	"sidebar_text_color",
	"navbar_background",
	"navbar_text_color",
	"page_background",
	"card_background",
	"text_color",
	"border_color",
	"accent_color",
)


class ThemeSettings(Document):
	def validate(self):
		if self.use_default_theme:
			return

		for fieldname in COLOR_FIELDS:
			value = self.get(fieldname)
			if value and not HEX_RE.match(value):
				frappe.throw(_("{0} is not a valid colour.").format(self.meta.get_label(fieldname)))

		if not self.accent_color:
			frappe.throw(_("Accent Colour is required when a custom theme is in use."))

	def on_update(self):
		# Values changed, not schema - nothing here ever needs a migration. Only
		# the generated CSS and the boot payload are stale, and both are cheap to
		# drop: the next request regenerates them.
		from frappe_themes.api import clear_theme_cache

		clear_theme_cache()
		frappe.clear_cache()

	def as_dict_for_css(self) -> dict:
		"""Plain values for :mod:`frappe_themes.theme_engine`."""
		return {fieldname: self.get(fieldname) for fieldname in self.meta.get_valid_columns()}
