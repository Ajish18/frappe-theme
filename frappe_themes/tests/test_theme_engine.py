# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from frappe_themes import theme_engine as te
from frappe_themes.standard_themes import PRESETS

SAMPLE_VALUES = {
	"use_default_theme": 0,
	"sidebar_background": "#0a4a30",
	"accent_color": "#00b964",
	"page_background": "#ffffff",
	"card_background": "#f7faf8",
	"text_color": "#15201b",
}


class TestColorMath(UnitTestCase):
	def test_readable_ink_picks_by_measured_contrast(self):
		self.assertEqual(te.readable_ink("#0a4a30"), "#ffffff")  # dark green -> white
		self.assertEqual(te.readable_ink("#f5f5f5"), "#000000")  # near white -> black

	def test_contrast_of_matches_wcag_formula(self):
		# Black on white is the maximum ratio, 21:1.
		self.assertAlmostEqual(te.contrast_of("#000000", "#ffffff"), 21.0, places=1)
		self.assertEqual(te.contrast_of("#123456", "#123456"), 1.0)

	def test_safe_button_color_fixes_low_contrast(self):
		# A bright green against white text fails AA outright.
		accent = "#00b964"
		white = "#ffffff"
		self.assertLess(te.contrast_of(accent, white), 4.5)

		button = te.safe_button_color(accent, white)
		self.assertGreaterEqual(te.contrast_of(button, white), 4.49)

	def test_safe_button_color_leaves_already_safe_colors_alone(self):
		accent = "#025a2f"  # already dark enough for white text
		self.assertEqual(te.safe_button_color(accent, "#ffffff"), accent)

	def test_mix_endpoints(self):
		self.assertEqual(te.mix("#000000", "#ffffff", 0), "#000000")
		self.assertEqual(te.mix("#000000", "#ffffff", 1), "#ffffff")

	def test_overlay_is_valid_rgba(self):
		result = te.overlay("#ffffff", 0.5)
		self.assertRegex(result, r"^rgba\(\d+, \d+, \d+, 0\.5\)$")


class TestBuildSettingsCss(UnitTestCase):
	def test_default_theme_emits_nothing(self):
		self.assertEqual(te.build_settings_css({"use_default_theme": 1}), "")
		self.assertEqual(te.build_settings_css({}), "")

	def test_active_theme_is_scoped(self):
		css = te.build_settings_css(SAMPLE_VALUES)
		self.assertIn('html[data-ft-active="1"]', css)
		for line in css.splitlines():
			stripped = line.strip()
			if stripped.endswith("{") and "/*" not in stripped:
				self.assertTrue(
					"data-ft-active" in stripped or ".page-card-head" in stripped or ".splash" in stripped,
					f"unscoped rule: {stripped}",
				)

	def test_accent_reaches_buttons_not_only_links(self):
		css = te.build_settings_css(SAMPLE_VALUES)
		self.assertIn("--btn-primary", css)
		self.assertIn("--primary:", css)

	def test_each_color_field_drives_its_own_token(self):
		css = te.build_settings_css(SAMPLE_VALUES)
		self.assertIn("--surface-base: #ffffff;", css)
		self.assertIn("--ink-gray-8: #15201b;", css)
		self.assertIn("--surface-sidebar: #0a4a30;", css)

	def test_independent_sidebar_and_navbar(self):
		"""Setting only the sidebar colour must not paint the navbar the same."""
		values = dict(SAMPLE_VALUES, navbar_background="#123456")
		css = te.build_settings_css(values)
		self.assertIn("#123456", css)
		# the navbar's own block sets --navbar-bg to its own colour, not the rail's
		navbar_block = css[css.index("/* navbar */") :]
		self.assertIn("#123456", navbar_block)

	def test_navbar_falls_back_to_sidebar_when_blank(self):
		"""The field's own description promises this."""
		values = {k: v for k, v in SAMPLE_VALUES.items() if k != "navbar_background"}
		css = te.build_settings_css(values)
		navbar_block = css[css.index("/* navbar */") :]
		self.assertIn(SAMPLE_VALUES["sidebar_background"], navbar_block)

	def test_navbar_own_color_does_not_leak_into_sidebar_tokens(self):
		values = dict(SAMPLE_VALUES, navbar_background="#123456")
		css = te.build_settings_css(values)
		navbar_block = css[css.index("/* navbar */") :]
		self.assertNotIn("--desk-sidebar-bg", navbar_block)
		self.assertIn("--navbar-bg: #123456;", navbar_block)

	def test_blank_sidebar_ink_is_computed_not_hardcoded(self):
		css = te.build_settings_css(SAMPLE_VALUES)  # sidebar_text_color left blank
		# dark green sidebar -> white ink
		self.assertIn("rgba(255, 255, 255,", css)

	def test_explicit_sidebar_ink_is_honoured(self):
		values = dict(SAMPLE_VALUES, sidebar_text_color="#ffd400")
		css = te.build_settings_css(values)
		r, g, b = te.to_rgb_tuple("#ffd400")
		self.assertIn(f"rgba({r}, {g}, {b},", css)

	def test_font_size_scales_the_ramp(self):
		base = te.build_settings_css(SAMPLE_VALUES)
		self.assertNotIn("--text-base:", base)

		bigger = te.build_settings_css(dict(SAMPLE_VALUES, base_font_size="17"))
		self.assertIn("--text-base: 17px;", bigger)

	def test_font_family_override(self):
		css = te.build_settings_css(dict(SAMPLE_VALUES, font_family="Serif"))
		self.assertIn("--font-stack:", css)
		self.assertIn("Georgia", css)

	def test_inter_default_emits_no_font_override(self):
		css = te.build_settings_css(dict(SAMPLE_VALUES, font_family="Inter (Default)"))
		self.assertNotIn("--font-stack:", css)

	def test_logo_css_only_when_toggled_on(self):
		values = dict(SAMPLE_VALUES, app_logo="/files/logo.png", show_logo_on_splash_screen=1)
		css = te.build_settings_css(values)
		self.assertIn("/files/logo.png", css)
		self.assertIn(".splash img", css)
		self.assertNotIn(".app-logo", css)  # login toggle left off

	def test_body_text_clears_aa_in_every_preset(self):
		for preset in PRESETS:
			values = dict(preset, use_default_theme=0)
			preview = te.get_preview(values)
			ratio = te.contrast_of(preview["text"], preview["page"])
			self.assertGreater(ratio, 4.5, f"{preset['label']}: body text only {ratio:.2f}:1")

	def test_sidebar_ink_clears_aa_in_every_preset(self):
		for preset in PRESETS:
			values = dict(preset, use_default_theme=0)
			preview = te.get_preview(values)
			ratio = te.contrast_of(preview["sidebar_ink"], preview["sidebar"])
			self.assertGreater(ratio, 4.5, f"{preset['label']}: sidebar text only {ratio:.2f}:1")

	def test_button_clears_aa_in_every_preset(self):
		for preset in PRESETS:
			values = dict(preset, use_default_theme=0)
			preview = te.get_preview(values)
			ink = te.readable_ink(preview["button"])
			ratio = te.contrast_of(preview["button"], ink)
			self.assertGreaterEqual(ratio, 4.49, f"{preset['label']}: button only {ratio:.2f}:1")


class TestThemeSettingsIntegration(IntegrationTestCase):
	def setUp(self):
		self._before = frappe.get_single("Theme Settings").as_dict_for_css()

	def tearDown(self):
		# `db.set_value` rather than `doc.save()`: cleanup restores whatever was
		# there before, unconditionally - it is not itself the thing under test,
		# so it has no business tripping the optimistic-lock check a real edit
		# should.
		frappe.db.set_single_value("Theme Settings", self._before)
		frappe.db.commit()

		from frappe_themes.api import clear_theme_cache

		clear_theme_cache()
		frappe.clear_cache()

	def test_default_state_is_the_stock_ui(self):
		doc = frappe.get_single("Theme Settings")
		doc.use_default_theme = 1
		doc.save(ignore_permissions=True)

		from frappe_themes.api import get_boot_info

		self.assertEqual(get_boot_info(), {"active": False, "css": ""})

	def test_saving_a_custom_theme_activates_it(self):
		doc = frappe.get_single("Theme Settings")
		doc.use_default_theme = 0
		doc.accent_color = "#00b964"
		doc.sidebar_background = "#0a4a30"
		doc.save(ignore_permissions=True)

		from frappe_themes.api import get_boot_info

		boot = get_boot_info()
		self.assertTrue(boot["active"])
		self.assertIn('html[data-ft-active="1"]', boot["css"])

	def test_invalid_color_is_rejected(self):
		doc = frappe.get_single("Theme Settings")
		doc.use_default_theme = 0
		doc.accent_color = "not-a-color"
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_missing_accent_is_rejected_for_custom_theme(self):
		doc = frappe.get_single("Theme Settings")
		doc.use_default_theme = 0
		doc.accent_color = None
		self.assertRaises(frappe.ValidationError, doc.save, ignore_permissions=True)

	def test_saving_invalidates_the_cache(self):
		from frappe_themes.api import get_active_css

		doc = frappe.get_single("Theme Settings")
		doc.reload()
		doc.use_default_theme = 0
		doc.accent_color = "#0d8ef8"
		doc.sidebar_background = "#12305c"
		doc.save(ignore_permissions=True)
		before = get_active_css()

		doc.reload()
		doc.accent_color = "#ff0000"
		doc.save(ignore_permissions=True)
		after = get_active_css()

		self.assertNotEqual(before, after)

	def test_preview_css_never_writes_to_the_database(self):
		from frappe_themes.api import preview_css

		before = frappe.get_single("Theme Settings").as_dict_for_css()
		preview_css({"use_default_theme": 0, "accent_color": "#ff00ff", "sidebar_background": "#111111"})
		after = frappe.get_single("Theme Settings").as_dict_for_css()
		self.assertEqual(before, after)

	def test_no_customization_leaks_onto_other_doctypes(self):
		"""Installation must not add a field to User or any other doctype - the
		whole app is one Single doctype plus additive CSS, nothing else."""
		self.assertFalse(frappe.db.exists("Custom Field", "User-frappe_theme"))
		module = frappe.get_all("Module Def", filters={"app_name": "frappe_themes"}, pluck="name")
		self.assertEqual(module, ["Frappe Themes"])
		doctypes = frappe.get_all("DocType", filters={"module": "Frappe Themes"}, pluck="name")
		self.assertEqual(doctypes, ["Theme Settings"])
