## Frappe Themes

Site-wide colour and branding settings for the Frappe Desk - one settings
page, no separate theme records to manage.

Open **Theme Settings**, turn off **Use Default Theme**, and pick a
colour for each named zone of the desk: Sidebar, Top Bar, Page & Records, and
Accent. Every field previews live on the real desk as you edit it - no
separate mock-up to imagine from. Save, confirm, done - it applies to every
user immediately. No reload, no `bench build`, no migration: the schema never
changes, only the values do.

### How it works

Frappe v16+ defines its colours as semantic CSS custom properties
(`--surface-*`, `--ink-*`, `--outline-*`, `--btn-primary`, ...). This app
overrides exactly those tokens with the literal colours you pick - nothing is
re-hued or derived from a formula. A colour you choose is the colour that
renders. Because Frappe UI apps and custom apps consume the same tokens, the
theme reaches them too, with no extra work.

What *is* computed automatically is whichever colour you leave blank - label
ink on a coloured background, a button-safe variant of the accent, muted text
- and it is computed by measured WCAG contrast against the surface it sits on,
never a fixed light/dark guess. That is what keeps sidebar text legible
whatever colour the sidebar is, and it is covered by the test suite.

### Installing

```bash
cd ~/frappe-bench
git clone https://github.com/Ajish18/frappe-catalogue.git apps/frappe_themes
bench pip install -e apps/frappe_themes
echo "frappe_themes" >> sites/apps.txt
bench --site <site> install-app frappe_themes
bench restart          # or restart `bench start` in development
```

(The repository is named `frappe-catalogue`; the app package is
`frappe_themes`. Clone into `apps/frappe_themes` as above so the folder name
matches what bench looks for - `bench get-app` on this URL will not resolve it
on its own.)

### Fields

| Section | Field | What it does |
|---|---|---|
| Sidebar | Background / Text Colour / Font Size | The panel on the left, and its slide-out on narrow screens |
| Top Bar | Background / Text Colour | The bar across the very top - independent of the sidebar, or leave blank to match it |
| Page & Records | Page Background / Card Background / Text Colour / Border Colour | The working area, records, columns and record data |
| Accent | Accent Colour | Buttons, links, focus rings, the selected sidebar row |
| Typography | Font / Base Font Size | Scales every size in the desk proportionally |
| Branding | Logo / Show on Splash Screen / Show on Login Page | Uploaded once, shown wherever you enable it |

**Load a preset** fills the colour pickers from one of ten starting points -
five light, five dark - as a draft to adjust and save, not a record of its
own.

### Scope and safety

- One Single doctype, one module, nothing written into any other doctype and
  no custom fields added to core doctypes (not even `User`) - installing this
  app changes nothing about how any other app behaves.
- **Use Default Theme** (on by default) shows stock, unmodified Frappe. Turning
  it off is the only thing that activates any override.
- Desk only. The website/portal has its own **Website Theme** doctype, and the
  login page's *layout* is untouched - only its logo is optionally swapped.
- Uninstalling removes the one doctype and nothing else.

### Development

```bash
bench --site <site> run-tests --app frappe_themes
```

### License

MIT
