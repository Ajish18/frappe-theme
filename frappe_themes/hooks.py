import os


def _versioned(path: str) -> str:
	"""`path`, with the file's own mtime as a cache-busting query string.

	These two files are plain, unbundled paths - deliberately, so the app needs
	no build step - which means Frappe never content-hashes their URL the way it
	does a `.bundle.js`. Without something changing the URL itself, a browser
	that has already cached the old copy (the default here is 12 hours) keeps
	using it even after the file on disk changes, silently running stale code
	against a boot payload it was not written for. The mtime is recomputed once,
	when this file is imported - which happens on every worker (re)start, i.e.
	exactly when a source change can actually reach a browser.
	"""
	full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public", path)
	try:
		version = int(os.path.getmtime(full_path))
	except OSError:
		version = 0
	return f"/assets/frappe_themes/{path}?v={version}"


app_name = "frappe_themes"
app_title = "Frappe Themes"
app_publisher = "Ajish"
app_description = "Site-wide colour and branding settings for Frappe Desk"
app_email = "ajishiyappan1@gmail.com"
app_license = "mit"

app_include_js = [_versioned("js/frappe_themes.js")]
app_include_css = [_versioned("css/frappe_themes.css")]

# The active theme's CSS rides along in boot - see frappe_themes/boot.py and
# frappe_themes/api.py.
extend_bootinfo = "frappe_themes.boot.extend_bootinfo"

after_install = "frappe_themes.install.after_install"
after_migrate = "frappe_themes.install.after_migrate"
before_uninstall = "frappe_themes.install.before_uninstall"
