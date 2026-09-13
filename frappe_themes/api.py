# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Theme resolution, caching and the endpoints the switcher talks to.

A theme is delivered as CSS in the boot payload rather than as a built asset.
That keeps it per-site (theme records live in the site database, not in the
bench), always current (no stale static file to invalidate) and free of any
build step - changing a colour takes effect on the next page load, with no
`bench build` and no `bench restart`.
"""

import frappe
from frappe import _

CACHE_KEY = "frappe_themes_css"
CATALOGUE_KEY = "frappe_themes_catalogue"


def get_theme_css(theme_name: str) -> str:
	"""Generated CSS for one theme, cached until the theme is edited."""
	if not theme_name:
		return ""

	cached = frappe.cache.hget(CACHE_KEY, theme_name)
	if cached is not None:
		return cached

	from frappe_themes.theme_engine import build_theme_css

	try:
		doc = frappe.get_cached_doc("Frappe Theme", theme_name)
	except frappe.DoesNotExistError:
		return ""

	css = build_theme_css(doc.as_spec()) if doc.enabled else ""
	frappe.cache.hset(CACHE_KEY, theme_name, css)
	return css


def clear_theme_cache(theme_name: str = None):
	if theme_name:
		frappe.cache.hdel(CACHE_KEY, theme_name)
	else:
		frappe.cache.delete_value(CACHE_KEY)
	frappe.cache.delete_value(CATALOGUE_KEY)


def resolve_theme(user: str = None) -> str | None:
	"""Which theme applies to `user`, honouring the site's override policy."""
	user = user or frappe.session.user
	if user == "Guest":
		# The desk is not served to guests, and the login page is deliberately
		# left alone - a themed login is a branding job, not a desk theme.
		return None

	settings = frappe.get_cached_doc("Frappe Theme Settings")
	if settings.enforce_default and not settings.allow_user_override:
		return settings.default_theme

	chosen = None
	if settings.allow_user_override:
		chosen = frappe.db.get_value("User", user, "frappe_theme")

	return chosen or settings.default_theme


def get_boot_info() -> dict:
	"""The blob the desk needs to paint the theme before anything renders."""
	theme_name = resolve_theme()
	if not theme_name:
		return {"slug": None, "css": "", "allow_user_override": 1}

	try:
		theme = frappe.get_cached_doc("Frappe Theme", theme_name)
	except frappe.DoesNotExistError:
		return {"slug": None, "css": "", "allow_user_override": 1}

	if not theme.enabled:
		return {"slug": None, "css": "", "allow_user_override": 1}

	settings = frappe.get_cached_doc("Frappe Theme Settings")
	return {
		"slug": theme.slug,
		"name": theme.name,
		"mode": theme.mode,
		"css": get_theme_css(theme.name),
		"allow_user_override": frappe.utils.cint(settings.allow_user_override),
	}


@frappe.whitelist()
def get_catalogue() -> list:
	"""Every enabled theme with its preview swatches and CSS, for the switcher.

	CSS travels with the list so the switcher can paint a live preview of a theme
	the moment it is highlighted, without a round trip per card.
	"""
	cached = frappe.cache.get_value(CATALOGUE_KEY)
	if cached:
		return cached

	from frappe_themes.theme_engine import build_theme_css, get_preview

	catalogue = []
	names = frappe.get_all(
		"Frappe Theme",
		filters={"enabled": 1},
		order_by="mode asc, is_standard desc, theme_name asc",
		pluck="name",
	)
	for name in names:
		doc = frappe.get_cached_doc("Frappe Theme", name)
		spec = doc.as_spec()
		catalogue.append(
			{
				"name": doc.name,
				"slug": doc.slug,
				"label": doc.theme_name,
				"description": doc.description,
				"mode": doc.mode,
				"sidebar_style": doc.sidebar_style,
				"is_standard": frappe.utils.cint(doc.is_standard),
				"preview": get_preview(spec),
				"css": build_theme_css(spec),
			}
		)

	frappe.cache.set_value(CATALOGUE_KEY, catalogue)
	return catalogue


@frappe.whitelist()
def set_user_theme(theme: str | None = None) -> dict:
	"""Apply a theme to the current user.

	`desk_theme` is kept in step with the theme's mode so the server-rendered
	`data-theme` on <html> is already right on the next load - the page never
	paints light before a dark theme arrives.
	"""
	settings = frappe.get_cached_doc("Frappe Theme Settings")
	if not settings.allow_user_override:
		frappe.throw(_("Theme selection is managed by your administrator."), frappe.PermissionError)

	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Guests cannot set a theme."), frappe.PermissionError)

	if theme and not frappe.db.exists("Frappe Theme", theme):
		frappe.throw(_("Theme {0} not found.").format(theme))

	frappe.db.set_value("User", user, "frappe_theme", theme or None, update_modified=False)

	if theme:
		mode = frappe.db.get_value("Frappe Theme", theme, "mode")
		frappe.db.set_value("User", user, "desk_theme", mode, update_modified=False)

	frappe.clear_cache(user=user)
	return get_boot_info()


@frappe.whitelist()
def rebuild_cache() -> str:
	"""Drop every cached stylesheet. Safe to call from `bench execute`."""
	frappe.only_for("System Manager")
	clear_theme_cache()
	return "ok"
