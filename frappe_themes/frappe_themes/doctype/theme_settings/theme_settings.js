// Copyright (c) 2026, Ajish and contributors
// For license information, please see license.txt

/**
 * Theme Settings - the form is the theme editor.
 *
 * Every colour field re-renders a small mock-up of the desk (rail, top bar,
 * a record card, a button) using the exact values on the form right now, and
 * live-previews them on the *real* desk behind the form - a colour picker
 * drives the actual UI, not a separate simulated one, so what you see really is
 * what saving gives you. Nothing is written to the database until Save, and
 * cancelling or navigating away reverts the live preview to whatever was last
 * saved.
 */

const FT_FIELDS = [
	"use_default_theme",
	"sidebar_background",
	"sidebar_text_color",
	"sidebar_font_size",
	"navbar_background",
	"navbar_text_color",
	"page_background",
	"card_background",
	"text_color",
	"border_color",
	"accent_color",
	"font_family",
	"base_font_size",
	"app_logo",
	"show_logo_on_splash_screen",
	"show_logo_on_login_page",
];

frappe.ui.form.on("Theme Settings", {
	refresh(frm) {
		frm.ft = frm.ft || new FrappeThemeEditor(frm);
		frm.ft.refresh();

		// The confirmation this doctype needs: the desk behind the form is
		// already showing the change, so "Save" here means "keep it" rather than
		// "guess what this will look like". Ctrl+S still saves directly - this
		// only wraps the visible button, which is how the vast majority of saves
		// on a settings form happen.
		frm.page.set_primary_action(__("Save"), () => frm.ft.confirm_and_save());
	},

	onload_post_render(frm) {
		FT_FIELDS.forEach((fieldname) => {
			frm.fields_dict[fieldname]?.$input?.on("change input", () => frm.ft?.on_field_change());
		});
	},

	before_save(frm) {
		// Belt-and-braces for Ctrl+S: still apply the live preview even when the
		// wrapped button above was bypassed.
		frm.ft?.preview();
	},

	after_save(frm) {
		frm.ft?.on_saved();
	},
});

class FrappeThemeEditor {
	constructor(frm) {
		this.frm = frm;
		this.debounced_preview = frappe.utils.debounce(() => this.preview(), 200);
	}

	refresh() {
		this.render_presets();
		this.render_mockup();
		this.preview();
	}

	on_field_change() {
		this.render_mockup();
		this.debounced_preview();
	}

	current_values() {
		const values = {};
		FT_FIELDS.forEach((fieldname) => (values[fieldname] = this.frm.doc[fieldname]));
		return values;
	}

	/** Push the form's current (unsaved) values onto the real desk. */
	preview() {
		frappe.xcall("frappe_themes.api.preview_css", { values: this.current_values() }).then((css) => {
			frappe.frappe_themes.apply(css);
		});
	}

	/** Confirm, save, then re-apply from what was actually persisted. */
	confirm_and_save() {
		const using_default = this.frm.doc.use_default_theme;
		const message = using_default
			? __("Switch everyone back to the default Frappe look?")
			: __(
					"The desk behind this form is already showing your changes. Save to apply them for every user - this takes effect immediately, no reload and no migration needed."
			  );

		frappe.confirm(message, () => {
			this.frm.save().then(() => {
				frappe.show_alert({ message: __("Theme saved and applied"), indicator: "green" }, 4);
			});
		});
	}

	on_saved() {
		frappe
			.xcall("frappe_themes.api.preview_css", { values: this.current_values() })
			.then((css) => frappe.frappe_themes.apply(css));
	}

	/** "Load a Preset" - fills the pickers client-side only; nothing is saved. */
	render_presets() {
		const $wrapper = this.frm.get_field("presets_html").$wrapper;
		if ($wrapper.data("ft-rendered")) return;
		$wrapper.data("ft-rendered", true);

		frappe.xcall("frappe_themes.api.get_presets").then((presets) => {
			const $row = $('<div class="ft-presets"></div>').appendTo($wrapper);
			$('<div class="ft-presets-label">' + __("Load a preset to start from") + "</div>").appendTo(
				$wrapper
			);

			presets.forEach((preset) => {
				const $swatch = $(`
					<button type="button" class="ft-preset" title="${frappe.utils.escape_html(preset.label)}">
						<span class="ft-preset-a" style="background:${preset.sidebar_background}"></span>
						<span class="ft-preset-b" style="background:${preset.accent_color}"></span>
					</button>
				`).appendTo($row);

				$swatch.on("click", () => this.apply_preset(preset));
			});
		});
	}

	apply_preset(preset) {
		["sidebar_background", "accent_color", "page_background", "card_background", "text_color"].forEach(
			(fieldname) => {
				if (preset[fieldname]) this.frm.set_value(fieldname, preset[fieldname]);
			}
		);
		this.frm.set_value("use_default_theme", 0);
		frappe.show_alert({ message: __("{0} loaded - review and Save to apply", [preset.label]) }, 4);
	}

	/** A miniature desk in the form itself, so the effect is visible without
	 * scrolling up to look at the real one, and so unsupported browsers/contexts
	 * (print view, a screenshot) still show something. */
	render_mockup() {
		const $field = this.frm.get_field("mockup_html").$wrapper;

		if (this.frm.doc.use_default_theme) {
			$field.hide();
			return;
		}
		$field.show();

		if (!this.$mockup_wrapper) {
			this.$mockup_wrapper = $('<div class="ft-mockup"></div>').appendTo($field);
		}
		const $wrapper = this.$mockup_wrapper;

		frappe
			.xcall("frappe_themes.api.get_preview_swatches", { values: this.current_values() })
			.then((p) => {
				$wrapper.html(`
					<div class="ft-mockup-shot" style="background:${p.page}">
						<div class="ft-mockup-rail" style="background:${p.sidebar}">
							<span class="ft-mockup-brand" style="background:${p.accent}"></span>
							<span class="ft-mockup-row active" style="background:${p.accent}"><i style="background:${p.button}"></i></span>
							<span class="ft-mockup-row"><i style="background:${p.sidebar_ink}"></i></span>
							<span class="ft-mockup-row"><i style="background:${p.sidebar_muted}"></i></span>
						</div>
						<div class="ft-mockup-main">
							<div class="ft-mockup-topbar" style="background:${p.navbar}">
								<i style="background:${p.navbar_ink}"></i>
							</div>
							<div class="ft-mockup-body">
								<span class="ft-mockup-title" style="background:${p.text}"></span>
								<span class="ft-mockup-btn" style="background:${p.button}"></span>
							</div>
							<div class="ft-mockup-card" style="background:${p.card};border-color:${p.border}">
								<i style="background:${p.muted}"></i>
								<i style="background:${p.muted}"></i>
								<i class="chip" style="background:${p.accent}"></i>
							</div>
						</div>
					</div>
					<div class="ft-mockup-caption">${__("Live preview - already applied to the desk behind this form")}</div>
				`);
			});
	}
}
