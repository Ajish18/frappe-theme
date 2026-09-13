// Copyright (c) 2026, Ajish and contributors
// For license information, please see license.txt

/**
 * Frappe Themes - desk client.
 *
 * Two jobs:
 *   1. Paint the user's theme as early as the desk lets us, from `frappe.boot`.
 *   2. Extend the stock theme switcher with the catalogue, rather than replace
 *      it - `user_settings_dialog.js` embeds a ThemeSwitcher and reads `.body`
 *      off it, so the class has to keep its shape.
 *
 * Themes are applied by writing `data-ft-theme` on <html> and injecting the
 * generated token block. Nothing is rebuilt and nothing is reloaded: every
 * colour in the desk resolves through a CSS custom property, so the whole UI
 * re-paints the moment the attribute changes.
 */

frappe.provide("frappe.frappe_themes");

(() => {
	const STYLE_ID = "frappe-themes-tokens";
	const ROOT = document.documentElement;

	/** Inject (or replace) the token block for the active theme. */
	function write_css(css) {
		let style = document.getElementById(STYLE_ID);
		if (!style) {
			style = document.createElement("style");
			style.id = STYLE_ID;
			// Last in <head> so it wins over the app stylesheets on equal specificity.
			document.head.appendChild(style);
		}
		style.textContent = css || "";
	}

	/**
	 * Apply a theme to the live document.
	 *
	 * `data-theme` is moved in step with the theme's mode so the Espresso base
	 * block underneath our overrides is the right one - a dark theme has to sit
	 * on the dark block, or the semantic aliases resolve to light-mode grays.
	 */
	function apply(theme) {
		if (!theme || !theme.slug) return clear();

		write_css(theme.css);
		ROOT.setAttribute("data-ft-theme", theme.slug);

		const mode = (theme.mode || "Light").toLowerCase();
		ROOT.setAttribute("data-theme", mode);
		ROOT.setAttribute("data-theme-mode", mode);
	}

	/** Drop back to stock Frappe. */
	function clear() {
		write_css("");
		ROOT.removeAttribute("data-ft-theme");
	}

	frappe.frappe_themes = {
		apply,
		clear,
		active: () => frappe.boot?.frappe_themes || null,
		get_catalogue() {
			if (this._catalogue) return Promise.resolve(this._catalogue);
			return frappe.xcall("frappe_themes.api.get_catalogue").then((themes) => {
				this._catalogue = themes;
				return themes;
			});
		},
	};

	// Paint immediately. This script is a blocking <script> that runs after the
	// inline boot payload and before the desk renders anything, so the tokens are
	// in place by the time there is a pixel to paint.
	const booted = frappe.boot?.frappe_themes;
	if (booted && booted.slug) apply(booted);
})();

/**
 * Catalogue-aware theme switcher.
 *
 * Extends the framework's so the dialog, keyboard navigation and the embed in
 * user settings keep working; only the card list, the card markup and what
 * happens on click are ours.
 */
frappe.frappe_themes.install_switcher = () => {
	const Base = frappe.ui.ThemeSwitcher;
	if (!Base || Base._ft_patched) return;

	frappe.ui.ThemeSwitcher = class FrappeThemesSwitcher extends Base {
		refresh() {
			this.current_theme = document.documentElement.getAttribute("data-ft-theme") || "__stock__";
			this.previous_theme = this.current_theme;
			this.fetch_themes().then(() => {
				this.body.empty();
				this.render();
			});
		}

		fetch_themes() {
			return frappe.frappe_themes.get_catalogue().then((themes) => {
				const stock = {
					name: "__stock__",
					label: __("Frappe Default"),
					info: __("The stock Frappe light theme"),
					mode: "Light",
					stock: true,
					preview: {
						page: "#ffffff",
						sidebar: "#f8f8f8",
						sidebar_ink: "#525252",
						accent: "#0d8ef8",
						ink: "#171717",
						muted: "#999999",
						outline: "#e2e2e2",
					},
				};

				// `name` is what the base class's keyboard handler compares on.
				this.themes = [stock].concat(
					themes.map((t) =>
						// `name` has to be the slug for the base class's keyboard
						// handler and for `data-ft-theme`; the doctype name is what
						// the server stores against the user, so keep both.
						Object.assign({}, t, {
							doc_name: t.name,
							name: t.slug,
							info: t.description || t.label,
						})
					)
				);
				return this.themes;
			});
		}

		get_preview_html(theme) {
			const selected = this.current_theme === theme.name;
			const p = theme.preview || {};
			const mode_label = theme.mode === "Dark" ? __("Dark") : __("Light");

			// The card is a miniature of the real layout - rail on the left, page on
			// the right - painted with the theme's own generated colours, so what is
			// on the card is what lands on the desk.
			const $card = $(`
				<div class="theme-card-wrapper ft-card-wrapper${selected ? " selected" : ""}">
					<button type="button" class="theme-card" title="${frappe.utils.escape_html(theme.info || "")}">
						<div class="theme-card-preview ft-preview" style="background:${p.page}">
							<div class="ft-preview-rail" style="background:${p.sidebar}">
								<span class="ft-dot" style="background:${p.accent}"></span>
								<span class="ft-line" style="background:${p.sidebar_ink}"></span>
								<span class="ft-line short" style="background:${p.sidebar_ink}"></span>
								<span class="ft-line short" style="background:${p.sidebar_ink}"></span>
							</div>
							<div class="ft-preview-page">
								<span class="ft-line wide" style="background:${p.ink}"></span>
								<span class="ft-line" style="background:${p.muted}"></span>
								<span class="ft-chip" style="background:${p.accent}"></span>
								<span class="ft-rule" style="background:${p.outline}"></span>
								<span class="ft-line" style="background:${p.muted}"></span>
							</div>
						</div>
						<div class="theme-card-footer">
							<span class="theme-card-label">
								${frappe.utils.escape_html(theme.label)}
								<small class="ft-mode">${mode_label}</small>
							</span>
							<span class="theme-card-radio"></span>
						</div>
					</button>
				</div>
			`);

			$card.on("click", () => {
				if (this.current_theme === theme.name) return;
				this.select(theme, $card);
			});

			return $card;
		}

		/** Preview on click, persist on confirm, revert on cancel. */
		select(theme, $card) {
			this.themes.forEach((th) => th.$html && th.$html.removeClass("selected"));
			$card.addClass("selected");

			frappe.frappe_themes.apply(theme.stock ? null : theme);
			this.current_theme = theme.name;

			frappe.confirm(
				__("Apply <b>{0}</b> to your desk?", [frappe.utils.escape_html(theme.label)]),
				() => this.commit(theme),
				() => this.revert()
			);
		}

		commit(theme) {
			frappe
				.xcall("frappe_themes.api.set_user_theme", { theme: theme.stock ? null : theme.doc_name })
				.then((applied) => {
					if (frappe.boot) frappe.boot.frappe_themes = applied;
					this.previous_theme = theme.name;
					frappe.show_alert({ message: __("Theme applied"), indicator: "green" }, 3);
				})
				.catch(() => {
					this.revert();
					frappe.show_alert({ message: __("Could not save theme"), indicator: "red" }, 5);
				});
		}

		revert() {
			const previous = this.themes.find((t) => t.name === this.previous_theme);
			frappe.frappe_themes.apply(previous && !previous.stock ? previous : null);
			this.current_theme = this.previous_theme;
			this.themes.forEach((th) => {
				if (!th.$html) return;
				th.$html.toggleClass("selected", th.name === this.previous_theme);
			});
		}
	};

	frappe.ui.ThemeSwitcher._ft_patched = true;
};

// desk.bundle.js is a blocking script ahead of this one, so the class is
// normally already there; the listener is the belt-and-braces path.
if (frappe.ui && frappe.ui.ThemeSwitcher) {
	frappe.frappe_themes.install_switcher();
} else {
	document.addEventListener("DOMContentLoaded", () => frappe.frappe_themes.install_switcher());
}
