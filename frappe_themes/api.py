# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Endpoints the settings form and the desk boot talk to.

One CSS-generating function - :func:`frappe_themes.theme_engine.build_settings_css`
- backs both a live, unsaved preview while editing and the real boot payload
after saving, so a preview is never wrong about what saving will do.
"""

import frappe
from frappe import _

CACHE_KEY = "frappe_themes_css"


def clear_theme_cache():
	frappe.cache.delete_value(CACHE_KEY)


def get_active_css() -> str:
	"""The generated CSS for the saved settings, cached until they change."""
	cached = frappe.cache.get_value(CACHE_KEY)
	if cached is not None:
		return cached

	from frappe_themes.theme_engine import build_settings_css

	settings = frappe.get_cached_doc("Theme Settings")
	css = build_settings_css(settings.as_dict_for_css())
	frappe.cache.set_value(CACHE_KEY, css)
	return css


def get_boot_info() -> dict:
	"""What the desk needs, attached to boot so the theme paints before anything
	else renders - see :mod:`frappe_themes.boot`."""
	try:
		settings = frappe.get_cached_doc("Theme Settings")
	except frappe.DoesNotExistError:
		return {"active": False, "css": ""}

	if settings.use_default_theme:
		return {"active": False, "css": ""}

	return {"active": True, "css": get_active_css()}


@frappe.whitelist()
def preview_css(values: dict | str) -> str:
	"""CSS for values the form has not saved yet - what a colour picker drives.

	Read-only and side-effect free: this never touches the database, so it is
	safe to call on every field change while a System Manager is still deciding.
	"""
	frappe.only_for("System Manager")

	if isinstance(values, str):
		values = frappe.parse_json(values)

	from frappe_themes.theme_engine import build_settings_css

	return build_settings_css(values or {})


@frappe.whitelist()
def get_presets() -> list:
	"""Starting points for the colour pickers - see standard_themes.py."""
	from frappe_themes.standard_themes import PRESETS

	return PRESETS


@frappe.whitelist()
def get_preview_swatches(values: dict | str) -> dict:
	"""The small set of colours the settings form's own mock-up paints with."""
	frappe.only_for("System Manager")

	if isinstance(values, str):
		values = frappe.parse_json(values)

	from frappe_themes.theme_engine import get_preview

	return get_preview(values or {})
