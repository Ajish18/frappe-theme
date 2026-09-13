# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Colour engine for Frappe Themes.

A theme is a *re-tint* of the Espresso token ramps that Frappe already ships,
not a hand-written palette. The base ramps are read straight out of
``frappe/public/css/espresso/colors.css`` when the stylesheet is generated, so a
theme keeps the lightness relationships - and therefore the contrast ratios -
that the framework was designed and tested with, and picks up ramp changes on
upgrade instead of drifting away from them.

Only the *raw* palette is re-tinted. The semantic layer (``--surface-*`` /
``--ink-*`` / ``--outline-*``) is declared in terms of the raw palette with
``var()``, so overriding ``--gray-500`` re-tints every surface, border and label
that resolves through it. Frappe UI apps consume the same tokens, so they are
themed by the same override with no extra work.
"""

import colorsys
import os
import re

import frappe

# Raw colour families we re-tint. `gray` carries every surface, border and text
# colour in the desk (`--btn-primary` is `--surface-gray-10`, i.e. gray-900), and
# `blue` is Espresso's interactive family - links, focus rings, active states.
NEUTRAL_FAMILY = "gray"
ACCENT_FAMILY = "blue"

# Matches `--gray-500: #aabbcc;` - only 3/6-digit hex, so `var()` aliases and
# the 8-digit alpha tokens (`--black-900: #000000e5`) are left alone.
TOKEN_RE = re.compile(r"--([a-z]+)-(\d+)\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\s*;")

LIGHT_BLOCK_RE = re.compile(r":root,\s*\[data-theme=\"light\"\]\s*\{(.*?)\n\}", re.S)
DARK_BLOCK_RE = re.compile(r"\[data-theme=\"dark\"\],\s*\.dark\s*\{(.*?)\n\}", re.S)


def get_colors_css_path() -> str:
	"""Path to the Espresso token source of truth in the installed frappe app."""
	return os.path.join(
		os.path.dirname(os.path.abspath(frappe.__file__)),
		"public",
		"css",
		"espresso",
		"colors.css",
	)


def parse_base_ramps() -> dict:
	"""Read the light and dark raw palettes out of Espresso's colors.css.

	Returns ``{"light": {"gray": {50: "#f8f8f8", ...}, ...}, "dark": {...}}``.
	Parsed once per process and cached - the file only changes on upgrade.
	"""
	if getattr(frappe.local, "_ft_base_ramps", None):
		return frappe.local._ft_base_ramps

	with open(get_colors_css_path()) as f:
		css = f.read()

	ramps = {}
	for mode, pattern in (("light", LIGHT_BLOCK_RE), ("dark", DARK_BLOCK_RE)):
		match = pattern.search(css)
		block = match.group(1) if match else ""
		families = {}
		for family, stop, value in TOKEN_RE.findall(block):
			families.setdefault(family, {})[int(stop)] = value
		ramps[mode] = families

	frappe.local._ft_base_ramps = ramps
	return ramps


# ---------------------------------------------------------------------------
# colour helpers
# ---------------------------------------------------------------------------


def hex_to_hls(value: str) -> tuple:
	value = value.strip().lstrip("#")
	if len(value) == 3:
		value = "".join(c * 2 for c in value)
	r, g, b = (int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))
	return colorsys.rgb_to_hls(r, g, b)


def hls_to_hex(h: float, l: float, s: float) -> str:
	r, g, b = colorsys.hls_to_rgb(h % 1.0, min(max(l, 0.0), 1.0), min(max(s, 0.0), 1.0))
	return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def relative_luminance(r: float, g: float, b: float) -> float:
	"""WCAG relative luminance for an sRGB triple in 0..1."""

	def channel(c):
		return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

	return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def match_luminance(hue: float, saturation: float, target: float) -> float:
	"""Lightness at which (hue, saturation) has `target` relative luminance.

	Rotating a hue at constant HSL lightness does not preserve how bright the
	colour *looks* - green at L=51% is far brighter than blue at L=51%, which is
	how a re-tinted ramp ends up neon. Luminance is monotonic in L for a fixed
	hue and saturation, so a short bisection lands on the lightness that keeps the
	stop as bright as the Espresso stop it replaces. That is what preserves the
	contrast ratios the framework was tested against.
	"""
	lo, hi = 0.0, 1.0
	for _ in range(24):
		mid = (lo + hi) / 2
		r, g, b = colorsys.hls_to_rgb(hue % 1.0, mid, saturation)
		if relative_luminance(r, g, b) < target:
			lo = mid
		else:
			hi = mid
	return (lo + hi) / 2


def neutral_saturation(chroma: float, lightness: float) -> float:
	"""Saturation for one neutral stop.

	A flat saturation across the ramp reads muddy in the mid tones and washed out
	in the darks, so the tint is weighted towards the dark end - the same shape
	Tailwind's `slate` and Radix's tinted grays use.
	"""
	return chroma * (0.55 + 0.9 * (1.0 - lightness))


def retint_ramp(base: dict, hue: float, *, chroma: float = None, sat_scale: float = 1.0) -> dict:
	"""Re-hue one ramp, keeping every stop's lightness.

	``chroma`` set  -> neutral mode: saturation is imposed (base grays have none).
	``chroma`` None -> accent mode: the base stop's own saturation is kept, so the
	ramp stays as vivid (and as carefully de-saturated at the ends) as Espresso's.
	"""
	out = {}
	for stop, value in base.items():
		r, g, b = (int(value.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4))
		_, l, s = colorsys.rgb_to_hls(r, g, b)
		if chroma is not None:
			new_s = neutral_saturation(chroma, l)
		else:
			new_s = min(1.0, s * sat_scale)
		new_l = match_luminance(hue, new_s, relative_luminance(r, g, b))
		out[stop] = hls_to_hex(hue, new_l, new_s)
	return out


def hue_of(color: str) -> float:
	return hex_to_hls(color)[0]


def saturation_of(color: str) -> float:
	return hex_to_hls(color)[2]


# ---------------------------------------------------------------------------
# stylesheet generation
# ---------------------------------------------------------------------------

ALIAS_RE = re.compile(r"--([a-z0-9-]+)\s*:\s*var\(--([a-z]+-\d+)\)\s*;")

# Semantic families repainted inside a contrast sidebar. Text, hover fills and
# borders - enough to make the panel legible on a dark rail without leaking dark
# tokens into anything else.
CONTRAST_ALIAS_PREFIXES = ("ink-gray-", "surface-gray-", "outline-gray-")

# Where a contrast sidebar's tokens apply. The panel, its flyout, the dock and
# the navbar - every surface painted with `--desk-sidebar-bg`.
CONTRAST_SCOPES = (".body-sidebar", ".sidebar-panel", ".dock-container", ".navbar")


def parse_alias_map(mode: str = "dark") -> dict:
	"""``{"ink-gray-9": "gray-50", ...}`` for one theme block.

	These are Espresso's own semantic assignments. Reusing them - rather than
	deciding for ourselves which gray a sidebar label should be - is what keeps a
	contrast sidebar consistent with Frappe's real dark mode.
	"""
	with open(get_colors_css_path()) as f:
		css = f.read()

	pattern = DARK_BLOCK_RE if mode == "dark" else LIGHT_BLOCK_RE
	match = pattern.search(css)
	return dict(ALIAS_RE.findall(match.group(1))) if match else {}


def build_ramps(spec: dict) -> dict:
	"""Generate the tinted neutral and accent ramps for a theme spec."""
	base = parse_base_ramps()
	mode = (spec.get("mode") or "Light").lower()
	base_mode = base.get(mode, base["light"])

	neutral_hue = hue_of(spec.get("neutral_tint") or "#808080")
	accent = spec.get("accent") or "#0d8ef8"

	ramps = {
		NEUTRAL_FAMILY: retint_ramp(
			base_mode.get(NEUTRAL_FAMILY, {}),
			neutral_hue,
			chroma=float(spec.get("neutral_chroma") or 0.05),
		),
		ACCENT_FAMILY: retint_ramp(base_mode.get(ACCENT_FAMILY, {}), hue_of(accent)),
	}

	# The contrast rail is painted with the *dark* neutral ramp whatever the
	# theme's own mode is - that is what a dark rail on a light page means.
	ramps["_contrast_neutral"] = retint_ramp(
		base["dark"].get(NEUTRAL_FAMILY, {}),
		neutral_hue,
		chroma=float(spec.get("neutral_chroma") or 0.05),
	)
	return ramps


def derive_sidebar_bg(spec: dict, ramps: dict) -> str:
	"""Explicit `sidebar_bg`, else the deep end of the theme's own neutral ramp."""
	if spec.get("sidebar_bg"):
		return spec["sidebar_bg"]
	contrast = ramps["_contrast_neutral"]
	return contrast.get(900) or contrast.get(950) or "#1f1f1f"


def build_theme_css(spec: dict) -> str:
	"""Full CSS for one theme, scoped to `html[data-ft-theme="<slug>"]`.

	The selector is one specificity step above Espresso's own `:root` /
	`[data-theme="light"]` blocks, so the overrides win without `!important` and
	without having to be loaded in any particular order.
	"""
	slug = spec["slug"]
	ramps = build_ramps(spec)
	root = f'html[data-ft-theme="{slug}"]'
	lines = [f"/* {spec.get('theme_name', slug)} - {spec.get('mode', 'Light').lower()} */", f"{root} {{"]

	for family in (NEUTRAL_FAMILY, ACCENT_FAMILY):
		for stop, value in sorted(ramps[family].items()):
			lines.append(f"\t--{family}-{stop}: {value};")

	accent_ramp = ramps[ACCENT_FAMILY]
	primary = accent_ramp.get(500) or spec.get("accent")
	# `--primary` is referenced by `--brand-color` and `--progress-bar-bg` but is
	# left undefined by the framework, so a theme is the only thing that sets it.
	lines.append(f"\t--primary: {primary};")
	lines.append(f"\t--primary-color: {primary};")

	is_contrast = (spec.get("sidebar_style") or "Match") == "Contrast"
	if is_contrast:
		sidebar_bg = derive_sidebar_bg(spec, ramps)
		lines.append(f"\t--desk-sidebar-bg: {sidebar_bg};")
		lines.append(f"\t--navbar-bg: {sidebar_bg};")
	lines.append("}")

	if is_contrast:
		lines.extend(build_contrast_css(spec, ramps, root))

	if spec.get("custom_css"):
		lines.append(f"/* custom css - {slug} */")
		lines.append(spec["custom_css"])

	return "\n".join(lines)


def build_contrast_css(spec: dict, ramps: dict, root: str) -> list:
	"""Repaint text, hover and border tokens inside a dark rail on a light theme."""
	aliases = parse_alias_map("dark")
	neutral = ramps["_contrast_neutral"]

	selector = ",\n".join(f"{root} {scope}" for scope in CONTRAST_SCOPES)
	lines = ["", f"/* {spec.get('theme_name')} - contrast sidebar */", f"{selector} {{"]

	for alias, target in sorted(aliases.items()):
		if not alias.startswith(CONTRAST_ALIAS_PREFIXES):
			continue
		family, _, stop = target.rpartition("-")
		if family != NEUTRAL_FAMILY:
			continue
		value = neutral.get(int(stop))
		if value:
			lines.append(f"\t--{alias}: {value};")

	# `--surface-sidebar` is `transparent` in dark so frappe-ui can let the page
	# show through; a rail drawn *over* a light page has to be opaque.
	lines.append(f"\t--surface-sidebar: {derive_sidebar_bg(spec, ramps)};")
	lines.append("}")
	return lines


def build_stylesheet(specs: list) -> str:
	"""The whole catalogue as one static stylesheet."""
	header = [
		"/* GENERATED by frappe_themes - do not edit.",
		" * Rebuild: bench --site <site> execute frappe_themes.api.rebuild_stylesheet",
		" */",
		"",
	]
	blocks = [build_theme_css(spec) for spec in specs]
	return "\n".join(header + blocks) + "\n"


def get_preview(spec: dict) -> dict:
	"""The handful of colours the picker paints a preview card with.

	Taken from the generated ramps rather than from the spec's raw inputs, so a
	card shows the colours the theme will actually render with.
	"""
	ramps = build_ramps(spec)
	neutral = ramps[NEUTRAL_FAMILY]
	accent = ramps[ACCENT_FAMILY]
	is_dark = (spec.get("mode") or "Light") == "Dark"
	is_contrast = (spec.get("sidebar_style") or "Match") == "Contrast"

	if is_contrast:
		sidebar = derive_sidebar_bg(spec, ramps)
	else:
		sidebar = neutral.get(900) if is_dark else neutral.get(50)

	return {
		"page": neutral.get(950) if is_dark else "#ffffff",
		"surface": neutral.get(900) if is_dark else neutral.get(50),
		"sidebar": sidebar,
		"sidebar_ink": ramps["_contrast_neutral"].get(200) if is_contrast else (
			neutral.get(200) if is_dark else neutral.get(700)
		),
		"accent": accent.get(500),
		"ink": neutral.get(50) if is_dark else neutral.get(900),
		"muted": neutral.get(400) if is_dark else neutral.get(500),
		"outline": neutral.get(700) if is_dark else neutral.get(300),
	}
