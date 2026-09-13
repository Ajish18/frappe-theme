# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""The themes Frappe Themes ships with.

Five light and five dark, paired across the same five hues so a site can move
between light and dark without the brand shifting. Each is defined by a handful
of inputs - an accent, a neutral tint and how hard to tint it - and the ramps are
generated from Espresso's own, see :mod:`frappe_themes.theme_engine`.

`sidebar_style = "contrast"` is what gives a light theme the dark branded rail
against a light working area. It is the default for the light themes because
that is the layout most business UIs use, and it is what keeps a light theme from
reading as plain white.
"""

STANDARD_THEMES = [
	# -- light -------------------------------------------------------------
	{
		"slug": "emerald-light",
		"theme_name": "Emerald Light",
		"description": "Deep green rail against a warm-neutral working area.",
		"mode": "Light",
		"accent": "#00b964",
		"neutral_tint": "#0d4f33",
		"neutral_chroma": 0.05,
		"sidebar_style": "Contrast",
		"sidebar_bg": "#064d32",
	},
	{
		"slug": "sapphire-light",
		"theme_name": "Sapphire Light",
		"description": "Navy rail with a clean blue accent. The classic ERP look.",
		"mode": "Light",
		"accent": "#0d8ef8",
		"neutral_tint": "#12305c",
		"neutral_chroma": 0.05,
		"sidebar_style": "Contrast",
		"sidebar_bg": "#0f2d54",
	},
	{
		"slug": "graphite-light",
		"theme_name": "Graphite Light",
		"description": "Neutral charcoal rail. Closest to stock Frappe, with more weight.",
		"mode": "Light",
		"accent": "#4b5563",
		"neutral_tint": "#1f2937",
		"neutral_chroma": 0.02,
		"sidebar_style": "Contrast",
		"sidebar_bg": "#1f2329",
	},
	{
		"slug": "plum-light",
		"theme_name": "Plum Light",
		"description": "Aubergine rail with a violet accent.",
		"mode": "Light",
		"accent": "#7c5cff",
		"neutral_tint": "#3b2a5c",
		"neutral_chroma": 0.05,
		"sidebar_style": "Contrast",
		"sidebar_bg": "#2e1f4d",
	},
	{
		"slug": "clay-light",
		"theme_name": "Clay Light",
		"description": "Warm terracotta rail on a paper-toned working area.",
		"mode": "Light",
		"accent": "#d2734a",
		"neutral_tint": "#5c3a2a",
		"neutral_chroma": 0.045,
		"sidebar_style": "Contrast",
		"sidebar_bg": "#4a2f21",
	},
	# -- dark --------------------------------------------------------------
	{
		"slug": "emerald-dark",
		"theme_name": "Emerald Dark",
		"description": "The Emerald palette, full dark.",
		"mode": "Dark",
		"accent": "#00b964",
		"neutral_tint": "#0d4f33",
		"neutral_chroma": 0.07,
		"sidebar_style": "Match",
	},
	{
		"slug": "sapphire-dark",
		"theme_name": "Sapphire Dark",
		"description": "Midnight navy with a blue accent.",
		"mode": "Dark",
		"accent": "#0d8ef8",
		"neutral_tint": "#12305c",
		"neutral_chroma": 0.07,
		"sidebar_style": "Match",
	},
	{
		"slug": "graphite-dark",
		"theme_name": "Graphite Dark",
		"description": "Neutral charcoal. Closest to stock Frappe dark.",
		"mode": "Dark",
		"accent": "#8a94a6",
		"neutral_tint": "#1f2937",
		"neutral_chroma": 0.02,
		"sidebar_style": "Match",
	},
	{
		"slug": "plum-dark",
		"theme_name": "Plum Dark",
		"description": "Deep aubergine with a violet accent.",
		"mode": "Dark",
		"accent": "#7c5cff",
		"neutral_tint": "#3b2a5c",
		"neutral_chroma": 0.07,
		"sidebar_style": "Match",
	},
	{
		"slug": "ember-dark",
		"theme_name": "Ember Dark",
		"description": "Warm dark with an amber accent, for long evenings in the desk.",
		"mode": "Dark",
		"accent": "#f5a623",
		"neutral_tint": "#4a2f21",
		"neutral_chroma": 0.06,
		"sidebar_style": "Match",
	},
]
