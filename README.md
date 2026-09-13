## Frappe Themes

A theme catalogue for the Frappe Desk. Ten curated themes - five light, five
dark - that a user picks from the theme switcher and sees applied immediately.

### How it works

Frappe v16+ defines its colours as Espresso design tokens: a raw palette
(`--gray-500`, `--blue-600`) with a semantic layer on top (`--surface-*`,
`--ink-*`, `--outline-*`) declared in terms of it with `var()`. Override the raw
palette and every surface, border, label and button that resolves through it
re-tints - including Frappe UI apps, which consume the same tokens.

So a theme here is not a stylesheet. It is a re-tint of the ramps the framework
already ships:

- The base ramps are read out of `frappe/public/css/espresso/colors.css` when a
  theme is generated, so themes track upstream across upgrades instead of
  drifting from it.
- Each stop keeps its **relative luminance**, not its HSL lightness. Rotating a
  hue at constant lightness is what makes re-tinted palettes look neon; matching
  luminance instead preserves the contrast ratios the framework was tested
  against. The test suite asserts this.
- Only the active theme's CSS is generated, and it travels in the boot payload.
  There is no build step, no generated file to invalidate, and themes stay
  per-site on a multi-site bench.

### Installing

The repository is named `frappe-catalogue` while the app package is
`frappe_themes`, so clone it into a folder matching the app name - `bench
get-app <url>` would clone into `apps/frappe-catalogue` and then try to install
from `apps/frappe_themes`:

```bash
cd ~/frappe-bench
git clone https://github.com/Ajish18/frappe-catalogue.git apps/frappe_themes
bench pip install -e apps/frappe_themes
echo "frappe_themes" >> sites/apps.txt
bench --site <site> install-app frappe_themes
bench restart          # or restart `bench start` in development
```

### Using it

Pick a theme from **Switch Theme** in the navbar, or from user settings. Cards
show the theme's own colours; clicking one previews it live and asks for
confirmation before saving.

### Sidebar styles

`Match` keeps the sidebar in step with the rest of the theme. `Contrast` paints
the sidebar and navbar dark against a light working area - the layout most
business UIs use - by overriding `--desk-sidebar-bg` and repainting the ink,
hover and border tokens inside the panel with Frappe's own dark-mode
assignments. All five light themes ship as `Contrast`.

### Making your own

Duplicate a theme (shipped ones are rewritten on every `bench migrate`, so edit a
copy) and set:

| Field | What it does |
|---|---|
| `Accent` | Links, focus rings, active states |
| `Neutral Tint` | Hue the greys are tinted towards |
| `Neutral Chroma` | How strongly. `0` is a pure grey, `0.05` is a subtle business tint, past `0.12` gets loud |
| `Sidebar Style` | `Match` or `Contrast` |
| `Custom CSS` | Appended to the theme's block, for anything the tokens do not cover |

### Administration

**Frappe Theme Settings** sets the site default, and can either allow users their
own choice or enforce one theme for everyone.

### Scope

Desk only. The website/portal has its own **Website Theme** doctype, and the
login page is left alone.

### Development

```bash
bench --site <site> run-tests --app frappe_themes
```

### License

MIT
