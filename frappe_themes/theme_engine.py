# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Turns Theme Settings into CSS.

The model is direct, not algorithmic: an administrator picks a literal colour
for each named zone of the desk - Sidebar, Navbar, Page & Records, Accent - and
that colour is what renders, exactly. Nothing is re-hued or derived from a
formula, because a formula is what produced the last version's surprise (every
theme rendering green regardless of what was picked).

What *is* still derived automatically - and this is the part worth keeping from
that version - is whichever colour the administrator leaves blank: label ink on
a coloured background, the safe button variant of an accent, muted text. Those
are computed by measured WCAG contrast against the surface they sit on, never a
fixed light/dark guess, so a colour that is picked always stays legible.

Only Frappe's own semantic tokens are touched (`--surface-*`, `--ink-*`,
`--outline-*`, `--btn-primary`, ...), never the raw palette. That is what makes
the theme apply to Frappe UI apps and custom apps for free: anything built on
those tokens picks it up without being told about this app.
"""

import frappe

# ---------------------------------------------------------------------------
# colour math
# ---------------------------------------------------------------------------


def _channels(color: str) -> tuple[float, float, float]:
	value = (color or "").strip().lstrip("#")
	if len(value) == 3:
		value = "".join(c * 2 for c in value)
	if len(value) != 6:
		return (0.5, 0.5, 0.5)
	return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def relative_luminance(color: str) -> float:
	"""WCAG relative luminance, 0 (black) to 1 (white)."""

	def channel(c):
		return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

	r, g, b = _channels(color)
	return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_of(a: str, b: str) -> float:
	"""WCAG contrast ratio between two colours, 1 (none) to 21 (max)."""
	la, lb = relative_luminance(a), relative_luminance(b)
	hi, lo = max(la, lb), min(la, lb)
	return (hi + 0.05) / (lo + 0.05)


def readable_ink(background: str) -> str:
	"""Pure black or pure white, whichever contrasts more with `background`."""
	if not background:
		return "#000000"
	return "#ffffff" if contrast_of(background, "#ffffff") >= contrast_of(background, "#000000") else "#000000"


def mix(a: str, b: str, weight: float) -> str:
	"""`a` blended towards `b` by `weight` (0 = pure a, 1 = pure b)."""
	ar, ag, ab = _channels(a)
	br, bg, bb = _channels(b)
	r, g, bl = (x + (y - x) * weight for x, y in ((ar, br), (ag, bg), (ab, bb)))
	return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(bl * 255))


def to_rgb_tuple(color: str) -> tuple[int, int, int]:
	r, g, b = _channels(color)
	return round(r * 255), round(g * 255), round(b * 255)


def overlay(ink: str, alpha: float) -> str:
	"""`ink` as a translucent layer, for dividers and hover states on a tinted rail.

	An overlay - rather than a flat colour - is what keeps every step at a
	predictable distance from whatever the rail's own colour is, brand colour
	included, without needing a colour of its own for each step.
	"""
	r, g, b = to_rgb_tuple(ink)
	return f"rgba({r}, {g}, {b}, {alpha:g})"


def safe_button_color(accent: str, ink: str, min_ratio: float = 4.5) -> str:
	"""`accent`, darkened or lightened just enough for `ink` text to read on it.

	A theme's accent is chosen for how it looks, not for whether text sits on it
	cleanly - so the button uses a shifted copy rather than the literal accent
	when the literal one would fail contrast.
	"""
	if contrast_of(accent, ink) >= min_ratio:
		return accent

	# Move towards whichever pole increases contrast: darker if the ink is light,
	# lighter if the ink is dark.
	target = "#000000" if relative_luminance(ink) > 0.5 else "#ffffff"
	for step in range(1, 20):
		candidate = mix(accent, target, step / 20)
		if contrast_of(candidate, ink) >= min_ratio:
			return candidate
	return target


# ---------------------------------------------------------------------------
# typography
# ---------------------------------------------------------------------------


def get_typography_css_path() -> str:
	import os

	return os.path.join(
		os.path.dirname(os.path.abspath(frappe.__file__)), "public", "css", "espresso", "typography.css"
	)


def parse_type_scale() -> dict:
	"""``{"text-base": 14, ...}`` - every px size Espresso's own ramp defines."""
	if getattr(frappe.local, "_ft_type_scale", None):
		return frappe.local._ft_type_scale

	import re

	try:
		with open(get_typography_css_path()) as f:
			scale = {name: int(px) for name, px in re.findall(r"--(text-[a-z0-9-]+)\s*:\s*(\d+)px\s*;", f.read())}
	except OSError:
		scale = {}

	frappe.local._ft_type_scale = scale
	return scale


def type_scale_css(base_font_size) -> list:
	"""Scale every desk font size proportionally around a new `--text-base`.

	The desk's sizes are a designed ramp, not independent numbers - scaling them
	all by the same factor keeps headings, labels and body text in the same
	relationship the framework was designed with, rather than growing body text
	while leaving headings behind.
	"""
	scale = parse_type_scale()
	anchor = scale.get("text-base", 14)
	if not scale or not base_font_size:
		return []

	base_font_size = float(base_font_size)
	if round(base_font_size) == anchor:
		return []

	factor = base_font_size / anchor
	return [f"\t--{name}: {round(px * factor)}px;" for name, px in sorted(scale.items())]


FONT_STACKS = {
	"Inter (Default)": None,  # Inter is already Espresso's own --font-stack.
	"System UI": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
	"Serif": 'Georgia, Cambria, "Times New Roman", Times, serif',
	"Monospace": '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace',
}


# ---------------------------------------------------------------------------
# CSS generation
# ---------------------------------------------------------------------------

ROOT_SELECTOR = 'html[data-ft-active="1"]'

# Everything the panel, its flyout and the navbar are painted with. `.dock` is
# the module switcher/rail in the current desk shell; `.body-sidebar` and
# `.sidebar-panel` are the in-app sidebar and its slide-out on narrow screens.
RAIL_SCOPES = (".body-sidebar", ".sidebar-panel", ".dock")
# The visible "top bar" in the current dock-based desk shell is `.page-head` -
# the sticky breadcrumb/title/actions strip at the top of every page - not
# `.navbar`, which is a thinner legacy element that is easy to mistake it for.
# Both are themed the same way so the setting means the same thing wherever
# the desk happens to render it.
NAVBAR_SCOPES = (".navbar", ".page-head")

# Ink steps as overlay alphas - `ink-gray-6` is the one that matters most,
# since `.item-anchor` colours every sidebar row label with it.
INK_ALPHAS = {9: 1.0, 8: 0.95, 7: 0.9, 6: 0.82, 5: 0.68, 4: 0.58, 3: 0.48, 2: 0.38, 1: 0.28}
SURFACE_ALPHAS = {1: 0.06, 2: 0.12, 3: 0.18, 4: 0.24, 5: 0.3}
OUTLINE_ALPHAS = {1: 0.12, 2: 0.18, 3: 0.24}


def rail_block(
	selectors: tuple,
	background: str,
	text_color: str | None,
	accent: str | None,
	*,
	own_tokens: tuple = (),
) -> list:
	"""Token overrides for one coloured rail (the sidebar, or the navbar).

	Every label, divider and hover state is an overlay of one ink colour over
	`background`, so the whole rail reads as one consistent surface whatever
	colour it is painted - the failure mode this replaces was a fixed grey that
	Frappe designed for near-black, applied on top of a bright accent instead.

	`own_tokens` are the surface-level tokens this particular rail is
	responsible for (`--desk-sidebar-bg` for the sidebar, `--navbar-bg` for the
	navbar) - kept separate per caller so the navbar's block does not also
	declare a sidebar token it has no reason to own, even though the two never
	actually conflict (the navbar block is emitted second, so it would win the
	cascade regardless).
	"""
	if not background:
		return []

	ink = text_color or readable_ink(background)
	selector = ",\n".join(f"{ROOT_SELECTOR} {s}" for s in selectors)
	lines = [selector + " {"]

	for stop, alpha in sorted(INK_ALPHAS.items()):
		lines.append(f"\t--ink-gray-{stop}: {overlay(ink, alpha)};")
	for stop, alpha in sorted(SURFACE_ALPHAS.items()):
		lines.append(f"\t--surface-gray-{stop}: {overlay(ink, alpha)};")
	for stop, alpha in sorted(OUTLINE_ALPHAS.items()):
		lines.append(f"\t--outline-gray-{stop}: {overlay(ink, alpha)};")

	for token in own_tokens:
		lines.append(f"\t{token}: {background};")

	if accent:
		lines.append(f"\t--surface-elevation-1: {overlay(ink, 0.08)};")
		lines.append(f"\t--surface-elevation-2: {overlay(ink, 0.14)};")
		# The selected row: `.active-sidebar` paints itself with
		# `--surface-elevation-3`, left alone that resolves to the *page's*
		# elevation-3 (usually near white), which is the white-pill-on-a-dark-rail
		# bug this replaces.
		lines.append(f"\t--surface-elevation-3: {accent};")
	lines.append("}")

	if accent:
		active_ink = readable_ink(accent)
		active_selector = ",\n".join(f"{ROOT_SELECTOR} {s} .active-sidebar" for s in selectors)
		lines.append(active_selector + " {")
		for stop in (6, 7, 8):
			lines.append(f"\t--ink-gray-{stop}: {active_ink};")
		lines.append("}")

	return lines


def build_settings_css(values: dict) -> str:
	"""The complete stylesheet for one set of settings values.

	Used for both the live preview while editing (unsaved values, called from
	the form) and the real boot payload (saved values) - one code path, so a
	preview is never wrong about what saving will do.
	"""
	if not values or values.get("use_default_theme"):
		return ""

	lines = [
		"/* GENERATED by frappe_themes - do not edit.",
		" * Regenerated automatically whenever Theme Settings is saved.",
		" */",
		"",
	]

	# --- page, records, and everything that is neither the rail nor the navbar
	page_bg = values.get("page_background")
	card_bg = values.get("card_background")
	text_color = values.get("text_color")
	border_color = values.get("border_color")
	accent = values.get("accent_color")

	global_lines = []
	if page_bg:
		global_lines.append(f"\t--surface-base: {page_bg};")
		# The subtle fills a page uses for list headers, hover rows and input
		# backgrounds are one step off the page colour, not off the card.
		muted_bg = mix(page_bg, readable_ink(page_bg), 0.06)
		muted_bg_2 = mix(page_bg, readable_ink(page_bg), 0.1)
		global_lines.append(f"\t--surface-gray-1: {muted_bg};")
		global_lines.append(f"\t--surface-gray-2: {muted_bg_2};")
	if card_bg:
		global_lines.append(f"\t--surface-elevation-1: {card_bg};")
		global_lines.append(f"\t--surface-elevation-2: {card_bg};")
		global_lines.append(f"\t--card-bg: {card_bg};")
	if text_color:
		global_lines.append(f"\t--ink-gray-8: {text_color};")
		global_lines.append(f"\t--ink-gray-9: {text_color};")
		against = page_bg or "#ffffff"
		global_lines.append(f"\t--ink-gray-6: {mix(text_color, against, 0.35)};")
		global_lines.append(f"\t--ink-gray-5: {mix(text_color, against, 0.5)};")
	if border_color:
		global_lines.append(f"\t--outline-gray-1: {border_color};")
		global_lines.append(f"\t--outline-gray-2: {border_color};")
	elif page_bg and text_color:
		auto_border = mix(page_bg, text_color, 0.15)
		global_lines.append(f"\t--outline-gray-1: {auto_border};")
		global_lines.append(f"\t--outline-gray-2: {auto_border};")
	if accent:
		global_lines.append(f"\t--primary: {accent};")
		global_lines.append(f"\t--primary-color: {accent};")

		button_color = values.get("button_color")
		# `.btn-primary` takes its own text colour from `--neutral`, which
		# Espresso flips by ambient light/dark mode - not by us - so we pin
		# `--neutral` too, to whichever pole actually reads on this button. That
		# decouples the button's legibility from the viewer's light/dark setting.
		if button_color:
			# Explicitly chosen: rendered exactly, never adjusted - the
			# administrator picked it, unlike the accent's own button fallback
			# below, which exists precisely because nobody picked one.
			btn_ink = readable_ink(button_color)
			button = button_color
		else:
			btn_ink = readable_ink(accent)
			button = safe_button_color(accent, btn_ink)
		global_lines.append(f"\t--btn-primary: {button};")
		global_lines.append(f"\t--progress-bar-bg: {button};")
		global_lines.append(f"\t--neutral: {btn_ink};")

	if global_lines:
		lines.append(ROOT_SELECTOR + " {")
		lines.extend(global_lines)
		lines.extend(type_scale_css(values.get("base_font_size")))
		font_stack = FONT_STACKS.get(values.get("font_family") or "Inter (Default)")
		if font_stack:
			lines.append(f"\t--font-stack: {font_stack};")
		lines.append("}")

	# --- sidebar
	rail_lines = rail_block(
		RAIL_SCOPES,
		values.get("sidebar_background"),
		values.get("sidebar_text_color"),
		accent,
		own_tokens=("--surface-sidebar", "--desk-sidebar-bg"),
	)
	if rail_lines:
		lines.append("")
		lines.append("/* sidebar */")
		lines.extend(rail_lines)

	sidebar_font = values.get("sidebar_font_size")
	if sidebar_font and values.get("sidebar_background"):
		selector = ",\n".join(f"{ROOT_SELECTOR} {s}" for s in RAIL_SCOPES)
		lines.append("")
		lines.append(selector + " {")
		lines.append(f"\t--text-sm: {int(float(sidebar_font))}px;")
		lines.append("}")

	# --- navbar (independent of the sidebar's own colour, but matches it by
	# default - "leave blank to match the sidebar" on the field itself)
	navbar_bg = values.get("navbar_background") or values.get("sidebar_background")
	navbar_ink = values.get("navbar_text_color") or (
		None if values.get("navbar_background") else values.get("sidebar_text_color")
	)
	navbar_lines = rail_block(
		NAVBAR_SCOPES,
		navbar_bg,
		navbar_ink,
		None,
		# `.page-head` - the breadcrumb/title strip that is the actual visible
		# "top bar" in the current dock-based desk shell - paints its background
		# from `--bg-color`/`--fg-color`, not from any token the sidebar's own
		# block touches, so the navbar colour has to reach those too or the
		# setting looks like it does nothing.
		own_tokens=("--navbar-bg", "--bg-color"),
	)
	if navbar_lines:
		lines.append("")
		lines.append("/* navbar */")
		lines.extend(navbar_lines)

	# --- branding
	logo = values.get("app_logo")
	if logo:
		if values.get("show_logo_on_splash_screen"):
			lines.append("")
			lines.append("/* splash screen logo */")
			lines.append(f'{ROOT_SELECTOR} .splash img {{ content: url("{logo}"); }}')
		if values.get("show_logo_on_login_page"):
			lines.append("")
			lines.append("/* login page logo */")
			lines.append(f'.page-card-head .app-logo {{ content: url("{logo}"); }}')
		if values.get("show_logo_as_app_icon"):
			lines.append("")
			lines.append("/* app icon - the mark shown top-left in the sidebar/dock */")
			# `.header-logo` is a plain container, not an <img> - dock.js fills it
			# with either an <img> (an app with its own logo_url) or an inline SVG
			# letter mark (one without). `content: url()` replaces whichever it is
			# with the uploaded image, so this works the same regardless of which
			# app is open, without needing to know how that app renders its own
			# icon.
			lines.append(f'{ROOT_SELECTOR} .dock-logo .header-logo {{ content: url("{logo}"); }}')

	return "\n".join(lines) + "\n"


def get_preview(values: dict) -> dict:
	"""The handful of swatches the settings form paints its live mock-up with."""
	page_bg = values.get("page_background") or "#ffffff"
	card_bg = values.get("card_background") or mix(page_bg, readable_ink(page_bg), 0.04)
	text_color = values.get("text_color") or readable_ink(page_bg)
	accent = values.get("accent_color") or "#0d8ef8"
	sidebar_bg = values.get("sidebar_background") or "#12305c"
	sidebar_ink = values.get("sidebar_text_color") or readable_ink(sidebar_bg)
	navbar_bg = values.get("navbar_background") or sidebar_bg
	navbar_ink = values.get("navbar_text_color") or readable_ink(navbar_bg)

	return {
		"page": page_bg,
		"card": card_bg,
		"text": text_color,
		"muted": mix(text_color, page_bg, 0.4),
		"border": values.get("border_color") or mix(page_bg, text_color, 0.15),
		"accent": accent,
		"button": values.get("button_color") or safe_button_color(accent, readable_ink(accent)),
		"sidebar": sidebar_bg,
		"sidebar_ink": sidebar_ink,
		"sidebar_muted": overlay(sidebar_ink, 0.55),
		"navbar": navbar_bg,
		"navbar_ink": navbar_ink,
	}
