app_name = "frappe_themes"
app_title = "Frappe Themes"
app_publisher = "Ajish"
app_description = "Theme catalogue for Frappe Desk and Frappe UI apps"
app_email = "ajishiyappan1@gmail.com"
app_license = "mit"

# Plain paths, not bundles: the switcher is small, has no imports to resolve and
# no SCSS to compile, so it needs no build step in the install.
app_include_js = ["/assets/frappe_themes/js/frappe_themes.js"]
app_include_css = ["/assets/frappe_themes/css/frappe_themes.css"]

# The active theme's CSS rides along in boot - see frappe_themes/api.py.
extend_bootinfo = "frappe_themes.boot.extend_bootinfo"

after_install = "frappe_themes.install.after_install"
after_migrate = "frappe_themes.install.after_migrate"
before_uninstall = "frappe_themes.install.before_uninstall"
