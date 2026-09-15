// Copyright (c) 2026, Ajish and contributors
// For license information, please see license.txt

/**
 * Frappe Themes - desk client.
 *
 * Two independent jobs:
 *
 *   1. Paint the saved theme as early as the desk lets us, from `frappe.boot`
 *      (every page load, every user).
 *   2. On the Theme Settings form itself, live-preview colours as they
 *      are picked - before saving - and apply them for real once a System
 *      Manager confirms.
 *
 * A theme is applied by writing one style block into <head> and setting
 * `data-ft-active` on <html>. Every colour in the desk resolves through a CSS
 * custom property, so the whole UI repaints the instant that block changes -
 * no reload, and nothing to rebuild.
 */

frappe.provide("frappe.frappe_themes");

(() => {
	const STYLE_ID = "frappe-themes-tokens";
	const ROOT = document.documentElement;

	function write_css(css) {
		let style = document.getElementById(STYLE_ID);
		if (!style) {
			style = document.createElement("style");
			style.id = STYLE_ID;
			document.head.appendChild(style);
		}
		style.textContent = css || "";
	}

	function apply(css) {
		if (!css) return clear();
		write_css(css);
		ROOT.setAttribute("data-ft-active", "1");
	}

	function clear() {
		write_css("");
		ROOT.removeAttribute("data-ft-active");
	}

	frappe.frappe_themes = { apply, clear };

	// Paint immediately, before the desk renders its first pixel.
	const boot = frappe.boot?.frappe_themes;
	if (boot && boot.active) apply(boot.css);
})();
