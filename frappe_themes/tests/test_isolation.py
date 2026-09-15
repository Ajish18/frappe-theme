# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Isolation: installing or using this app must not change how any other app
- core Frappe, ERPNext, or a third-party custom app - behaves.

Grounded in what the app actually is: one Single doctype, one static
stylesheet scoped entirely under `.ft-` classes, and CSS injected into the
boot payload that is empty unless an administrator has explicitly turned the
theme on. There is no fixture, no custom field on any other doctype, no
lifecycle hook on any other doctype's events, and no monkeypatching. These
tests assert that contract directly, so a future change that quietly widens
it - a `doc_events` entry, a fixture, a field bolted onto `User` again - fails
here instead of surfacing as a surprise on somebody else's site.
"""

import inspect
import os
import re

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

import frappe_themes.hooks as hooks_module

# A sample of doctypes this app must never be seen anywhere near: Frappe core,
# a few of ERPNext's, and the two settings doctypes a theme app is most
# tempted to write into instead of asking (Website Settings, Navbar Settings -
# both already carry their own logo/branding fields, which is exactly why
# writing into them would be scope creep instead of isolation).
FOREIGN_DOCTYPES = (
	"User",
	"System Settings",
	"Website Settings",
	"Navbar Settings",
	"Role",
	"Item",
	"Customer",
	"Sales Invoice",
)

# Hook names that would mean this app is reaching into another doctype's
# lifecycle, permissions, or request handling. None of them describe anything
# a colour-and-branding settings page legitimately needs.
LIFECYCLE_HOOK_NAMES = (
	"doc_events",
	"override_doctype_class",
	"override_whitelisted_methods",
	"standard_queries",
	"permission_query_conditions",
	"has_permission",
	"before_request",
	"after_request",
	"on_session_creation",
	"on_login",
	"on_logout",
	"scheduler_events",
	"fixtures",
	"notification_config",
	"jinja",
	"website_route_rules",
	"standard_portal_menu_items",
)

# What this app is allowed to declare. Anything outside this set is either a
# private helper (leading underscore, a function) or a genuine expansion of
# scope that deserves a human looking at it before it ships.
EXPECTED_HOOK_NAMES = {
	"app_name",
	"app_title",
	"app_publisher",
	"app_description",
	"app_email",
	"app_license",
	"app_include_js",
	"app_include_css",
	"extend_bootinfo",
	"after_install",
	"after_migrate",
	"before_uninstall",
}


class TestHooksIsolation(UnitTestCase):
	"""Static checks against hooks.py itself - no site needed."""

	def test_only_expected_hooks_are_declared(self):
		declared = {
			name
			for name in vars(hooks_module)
			if not name.startswith("_")
			and not callable(getattr(hooks_module, name))
			and not inspect.ismodule(getattr(hooks_module, name))
		}
		unexpected = declared - EXPECTED_HOOK_NAMES
		self.assertEqual(unexpected, set(), f"hooks.py declares unreviewed hooks: {unexpected}")

	def test_no_lifecycle_hooks_on_other_doctypes(self):
		for hook_name in LIFECYCLE_HOOK_NAMES:
			self.assertFalse(
				hasattr(hooks_module, hook_name),
				f"hooks.py declares '{hook_name}' - this app has no business in another "
				f"doctype's lifecycle, permissions, or request handling.",
			)

	def test_boot_hook_points_at_our_own_module_only(self):
		self.assertEqual(hooks_module.extend_bootinfo, "frappe_themes.boot.extend_bootinfo")

	def test_included_assets_are_ours_only(self):
		for path in hooks_module.app_include_js + hooks_module.app_include_css:
			self.assertTrue(
				path.startswith("/assets/frappe_themes/"),
				f"app_include asset '{path}' is not one of this app's own files",
			)


class TestBootIsolation(UnitTestCase):
	"""extend_bootinfo must be purely additive - one new key, nothing touched."""

	def test_extend_bootinfo_only_adds_its_own_key(self):
		from frappe_themes.boot import extend_bootinfo

		# A stand-in for the boot payload other apps have already populated by
		# the time ours runs - `extend_bootinfo` hooks run in sequence, and
		# nothing here should depend on running first or last.
		bootinfo = frappe._dict(
			{
				"user": {"name": "test@example.com"},
				"sysdefaults": {"currency": "INR"},
				"desk_theme": "Light",
				"apps_data": {"apps": []},
			}
		)
		before = dict(bootinfo)

		extend_bootinfo(bootinfo)

		for key, value in before.items():
			self.assertEqual(bootinfo[key], value, f"extend_bootinfo mutated existing boot key '{key}'")
		self.assertIn("frappe_themes", bootinfo)
		self.assertEqual(set(bootinfo.keys()) - set(before.keys()), {"frappe_themes"})

	def test_extend_bootinfo_never_raises(self):
		"""A theme is cosmetic - it must never be able to take the desk down."""
		from frappe_themes.boot import extend_bootinfo

		for garbage in (frappe._dict(), frappe._dict({"user": None}), frappe._dict({"weird": object()})):
			try:
				extend_bootinfo(garbage)
			except Exception as e:  # noqa: BLE001 - the point of the test is that nothing escapes
				self.fail(f"extend_bootinfo raised on malformed bootinfo: {e!r}")


class TestStylesheetIsolation(UnitTestCase):
	"""The static CSS loads on every desk page (`app_include_css`) - every rule
	in it must therefore be scoped so it cannot paint anything outside this
	app's own components."""

	def get_selectors(self) -> list:
		path = os.path.join(
			os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "css", "frappe_themes.css"
		)
		with open(path) as f:
			css = f.read()
		css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)  # strip comments
		blocks = re.findall(r"([^{}]+)\{", css)
		selectors = []
		for block in blocks:
			selectors.extend(s.strip() for s in block.split(",") if s.strip())
		return selectors

	def test_every_selector_is_scoped_to_our_own_classes(self):
		selectors = self.get_selectors()
		self.assertGreater(len(selectors), 0, "no selectors found - the parser or the file moved")

		for selector in selectors:
			first_token = selector.split()[0]
			self.assertTrue(
				first_token.startswith(".ft-"),
				f"unscoped selector in the global stylesheet: '{selector}' - "
				f"this file loads on every desk page, so anything not scoped under "
				f".ft- can paint someone else's UI.",
			)


class TestDatabaseIsolation(IntegrationTestCase):
	"""What actually ended up in the database after installing this app."""

	def test_no_custom_field_on_foreign_doctypes(self):
		for doctype in FOREIGN_DOCTYPES:
			fields = frappe.get_all(
				"Custom Field", filters={"dt": doctype}, fields=["fieldname", "module"]
			)
			ours = [f for f in fields if "theme" in (f.fieldname or "").lower() or f.module == "Frappe Themes"]
			self.assertEqual(ours, [], f"{doctype} carries a Custom Field from this app: {ours}")

	def test_no_property_setter_from_this_app(self):
		setters = frappe.get_all("Property Setter", filters={"module": "Frappe Themes"})
		self.assertEqual(setters, [])

	def test_no_client_script_from_this_app(self):
		scripts = frappe.get_all("Client Script", filters={"module": "Frappe Themes"})
		self.assertEqual(scripts, [])

	def test_module_owns_exactly_one_doctype(self):
		doctypes = frappe.get_all("DocType", filters={"module": "Frappe Themes"}, pluck="name")
		self.assertEqual(doctypes, ["Theme Settings"])

	def test_no_page_or_report_from_this_app(self):
		"""A prior version of this app shipped a Theme Gallery page - gone now,
		and nothing should have taken its place without a deliberate decision."""
		pages = frappe.get_all("Page", filters={"module": "Frappe Themes"}, pluck="name")
		reports = frappe.get_all("Report", filters={"module": "Frappe Themes"}, pluck="name")
		self.assertEqual(pages, [])
		self.assertEqual(reports, [])

	def test_foreign_doctype_metadata_is_untouched(self):
		"""Spot-check: opening a foreign doctype's meta must not show any field,
		link, or permission row this app could plausibly have added."""
		meta = frappe.get_meta("User")
		suspicious = [df.fieldname for df in meta.fields if "frappe_theme" in (df.fieldname or "")]
		self.assertEqual(suspicious, [], "User carries a field this app appears to have added")

	def test_use_default_theme_produces_no_css_for_anyone(self):
		"""The one behavioural switch that matters: off means truly off, not
		'off but still injecting something'."""
		from frappe_themes.api import get_boot_info

		before = frappe.get_single("Theme Settings").as_dict_for_css()
		doc = frappe.get_single("Theme Settings")
		doc.use_default_theme = 1
		doc.save(ignore_permissions=True)
		try:
			boot = get_boot_info()
			self.assertEqual(boot, {"active": False, "css": ""})
		finally:
			frappe.db.set_single_value("Theme Settings", before)
			frappe.db.commit()
			from frappe_themes.api import clear_theme_cache

			clear_theme_cache()
