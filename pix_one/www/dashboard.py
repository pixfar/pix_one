import frappe
import os
import re

def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    context.title = "Dashboard"

    # Read the built index.html to get the current asset filenames
    app_path = frappe.get_app_path("pix_one")
    index_html_path = os.path.join(app_path, "public", "dashboard", "index.html")

    if os.path.exists(index_html_path):
        with open(index_html_path, 'r') as f:
            content = f.read()

        # Extract JS and CSS filenames (they already have full paths from Vite build)
        js_match = re.search(r'src="(/assets/[^"]+\.js)"', content)
        css_match = re.search(r'href="(/assets/[^"]+\.css)"', content)

        if js_match:
            context.js_file = js_match.group(1)
        if css_match:
            context.css_file = css_match.group(1)

    return context
