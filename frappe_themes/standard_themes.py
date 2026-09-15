# Copyright (c) 2026, Ajish and contributors
# For license information, please see license.txt
"""Preset colour sets.

Not stored as records and never applied on their own - these only fill the
Frappe Theme Settings form's colour pickers as a starting point (see
`presets_html` on the doctype and the "Load a Preset" buttons it renders). An
administrator still reviews, adjusts and saves; nothing here writes to the
database by itself.
"""

PRESETS = [
	{
		"key": "emerald",
		"label": "Emerald",
		"sidebar_background": "#0a4a30",
		"accent_color": "#00b964",
		"page_background": "#ffffff",
		"card_background": "#f7faf8",
		"text_color": "#15201b",
	},
	{
		"key": "sapphire",
		"label": "Sapphire",
		"sidebar_background": "#0f2d54",
		"accent_color": "#0d8ef8",
		"page_background": "#ffffff",
		"card_background": "#f7f9fb",
		"text_color": "#171a20",
	},
	{
		"key": "graphite",
		"label": "Graphite",
		"sidebar_background": "#1f2329",
		"accent_color": "#4b5563",
		"page_background": "#ffffff",
		"card_background": "#f8f8f8",
		"text_color": "#171717",
	},
	{
		"key": "plum",
		"label": "Plum",
		"sidebar_background": "#2e1f4d",
		"accent_color": "#7c5cff",
		"page_background": "#ffffff",
		"card_background": "#f9f8fb",
		"text_color": "#1b1721",
	},
	{
		"key": "clay",
		"label": "Clay",
		"sidebar_background": "#4a2f21",
		"accent_color": "#d2734a",
		"page_background": "#fffdfb",
		"card_background": "#faf6f2",
		"text_color": "#211712",
	},
	{
		"key": "emerald-dark",
		"label": "Emerald (Dark desk)",
		"sidebar_background": "#0a3d27",
		"accent_color": "#00b964",
		"page_background": "#14181a",
		"card_background": "#1b2321",
		"text_color": "#f2f5f3",
	},
	{
		"key": "sapphire-dark",
		"label": "Sapphire (Dark desk)",
		"sidebar_background": "#0d2444",
		"accent_color": "#349bef",
		"page_background": "#12161c",
		"card_background": "#1a212b",
		"text_color": "#eef2f7",
	},
	{
		"key": "graphite-dark",
		"label": "Graphite (Dark desk)",
		"sidebar_background": "#15181c",
		"accent_color": "#8a94a6",
		"page_background": "#121314",
		"card_background": "#1a1c1f",
		"text_color": "#f0f0f0",
	},
	{
		"key": "plum-dark",
		"label": "Plum (Dark desk)",
		"sidebar_background": "#241941",
		"accent_color": "#9b85f5",
		"page_background": "#141018",
		"card_background": "#1e1826",
		"text_color": "#f1eef7",
	},
	{
		"key": "ember-dark",
		"label": "Ember (Dark desk)",
		"sidebar_background": "#3a2519",
		"accent_color": "#f5a623",
		"page_background": "#191512",
		"card_background": "#231b16",
		"text_color": "#f7f1ea",
	},
]
