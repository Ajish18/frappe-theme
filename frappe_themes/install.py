# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Installation.

Deliberately minimal: one Single doctype, its own module, nothing written into
any other doctype's data and no custom fields on core doctypes. That is what
lets this app be installed on any site - alongside any other app, custom or
core - without touching how that app behaves: everything here is additive CSS,
switched on only once an administrator turns off "Use Default Theme".
"""

import frappe

DEFAULTS = {
	"use_default_theme": 1,
	"accent_color": "#0d8ef8",
	"sidebar_background": "#12305c",
	"page_background": "#ffffff",
	"card_background": "#f8f8f8",
	"text_color": "#171717",
}


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	settings = frappe.get_single("Theme Settings")
	changed = False
	for fieldname, value in DEFAULTS.items():
		if not settings.get(fieldname):
			settings.set(fieldname, value)
			changed = True
	if changed:
		settings.save(ignore_permissions=True)

	from frappe_themes.api import clear_theme_cache

	clear_theme_cache()


def before_uninstall():
	from frappe_themes.api import clear_theme_cache

	clear_theme_cache()
