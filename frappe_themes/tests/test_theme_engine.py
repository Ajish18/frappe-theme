# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from frappe_themes import theme_engine as te
from frappe_themes.standard_themes import STANDARD_THEMES


def contrast_ratio(a: str, b: str) -> float:
	def lum(value):
		r, g, b_ = (int(value.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
		return te.relative_luminance(r, g, b_)

	la, lb = lum(a), lum(b)
	hi, lo = max(la, lb), min(la, lb)
	return (hi + 0.05) / (lo + 0.05)


class TestThemeEngine(UnitTestCase):
	def test_base_ramps_parse(self):
		"""The Espresso token file is the input to everything else."""
		ramps = te.parse_base_ramps()
		for mode in ("light", "dark"):
			self.assertIn("gray", ramps[mode])
			self.assertIn("blue", ramps[mode])
			# 50 through 950 - the ramp Frappe actually ships.
			self.assertGreaterEqual(len(ramps[mode]["gray"]), 11)
			for value in ramps[mode]["gray"].values():
				self.assertRegex(value, r"^#[0-9a-f]{6}$")

	def test_retint_preserves_luminance(self):
		"""A re-tinted stop is as bright as the stop it replaces.

		This is the property the whole approach rests on: keep every stop's
		luminance and the contrast ratios Frappe was designed against survive the
		re-tint, whatever hue the theme uses.
		"""
		base = te.parse_base_ramps()
		for spec in STANDARD_THEMES:
			ramps = te.build_ramps(spec)
			base_mode = base[spec["mode"].lower()]
			for family in (te.NEUTRAL_FAMILY, te.ACCENT_FAMILY):
				for stop, value in ramps[family].items():
					drift = abs(
						contrast_ratio(value, "#ffffff") - contrast_ratio(base_mode[family][stop], "#ffffff")
					)
					self.assertLess(
						drift,
						0.35,
						f"{spec['slug']} {family}-{stop} drifted {drift:.2f} from upstream",
					)

	def test_body_text_stays_accessible(self):
		"""Body text on the page background clears WCAG AA in every theme."""
		for spec in STANDARD_THEMES:
			ramps = te.build_ramps(spec)
			preview = te.get_preview(spec)
			ratio = contrast_ratio(preview["ink"], preview["page"])
			self.assertGreater(ratio, 4.5, f"{spec['slug']} body text only {ratio:.2f}:1")

	def test_contrast_sidebar_is_legible(self):
		"""Sidebar labels clear AA against the dark rail they sit on."""
		for spec in STANDARD_THEMES:
			if spec.get("sidebar_style") != "Contrast":
				continue
			preview = te.get_preview(spec)
			ratio = contrast_ratio(preview["sidebar_ink"], preview["sidebar"])
			self.assertGreater(ratio, 4.5, f"{spec['slug']} sidebar text only {ratio:.2f}:1")

	def test_css_is_scoped_to_the_theme(self):
		"""Nothing may leak outside the theme's own attribute selector."""
		for spec in STANDARD_THEMES:
			css = te.build_theme_css(spec)
			self.assertIn(f'html[data-ft-theme="{spec["slug"]}"]', css)
			for line in css.splitlines():
				stripped = line.strip()
				if stripped.endswith("{"):
					self.assertIn(
						"data-ft-theme",
						stripped,
						f"{spec['slug']} emits an unscoped rule: {stripped}",
					)

	def test_contrast_themes_repaint_the_rail(self):
		for spec in STANDARD_THEMES:
			css = te.build_theme_css(spec)
			if spec.get("sidebar_style") == "Contrast":
				self.assertIn("--desk-sidebar-bg", css)
				self.assertIn(".body-sidebar", css)
				self.assertIn("--ink-gray-9", css)
			else:
				self.assertNotIn(".body-sidebar", css)

	def test_every_standard_theme_is_distinct(self):
		slugs = [s["slug"] for s in STANDARD_THEMES]
		self.assertEqual(len(slugs), len(set(slugs)))
		self.assertEqual(len([s for s in STANDARD_THEMES if s["mode"] == "Light"]), 5)
		self.assertEqual(len([s for s in STANDARD_THEMES if s["mode"] == "Dark"]), 5)


class TestThemeIntegration(IntegrationTestCase):
	def test_standard_themes_installed(self):
		for spec in STANDARD_THEMES:
			self.assertTrue(
				frappe.db.exists("Frappe Theme", spec["theme_name"]),
				f"{spec['theme_name']} was not installed",
			)

	def test_user_field_exists(self):
		self.assertTrue(frappe.db.exists("Custom Field", "User-frappe_theme"))

	def test_slug_is_generated(self):
		doc = frappe.get_doc(
			{
				"doctype": "Frappe Theme",
				"theme_name": "Test Slug Theme",
				"mode": "Light",
				"accent": "#00b964",
				"neutral_tint": "#0d4f33",
			}
		).insert()
		self.addCleanup(lambda: frappe.delete_doc("Frappe Theme", doc.name, force=True))
		self.assertEqual(doc.slug, "test-slug-theme")

	def test_boot_payload_carries_css(self):
		"""What the desk receives is a slug plus the CSS to paint it with."""
		from frappe_themes.api import get_boot_info

		frappe.db.set_value("User", "Administrator", "frappe_theme", "Emerald Light")
		frappe.clear_cache(user="Administrator")
		self.addCleanup(
			lambda: frappe.db.set_value("User", "Administrator", "frappe_theme", None)
		)

		boot = get_boot_info()
		self.assertEqual(boot["slug"], "emerald-light")
		self.assertEqual(boot["mode"], "Light")
		self.assertIn('html[data-ft-theme="emerald-light"]', boot["css"])
		self.assertIn("--desk-sidebar-bg", boot["css"])

	def test_catalogue_shape(self):
		from frappe_themes.api import get_catalogue

		frappe.cache.delete_value("frappe_themes_catalogue")
		catalogue = get_catalogue()
		self.assertGreaterEqual(len(catalogue), 10)
		for entry in catalogue:
			for key in ("slug", "label", "mode", "preview", "css"):
				self.assertIn(key, entry)
			for swatch in ("page", "sidebar", "accent", "ink"):
				self.assertRegex(entry["preview"][swatch], r"^#[0-9a-f]{6}$")

	def test_editing_a_theme_invalidates_its_cache(self):
		from frappe_themes.api import get_theme_css

		before = get_theme_css("Emerald Light")
		doc = frappe.get_doc("Frappe Theme", "Emerald Light")
		original = doc.accent
		doc.accent = "#ff0000"
		doc.save()
		self.addCleanup(lambda: self._restore(original))

		after = get_theme_css("Emerald Light")
		self.assertNotEqual(before, after, "cached CSS survived an edit")

	def _restore(self, accent):
		doc = frappe.get_doc("Frappe Theme", "Emerald Light")
		doc.accent = accent
		doc.save()
