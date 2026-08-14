"""Redirect stubs for moved pages — redirect-on-move discipline.

Every URL this site has ever published keeps serving: when a page moves,
its old URL gets a meta-refresh stub pointing at the new home. Add an
entry to STUBS whenever a page moves; never remove entries (partners and
customers hold these URLs in mails, bookmarks and KIS configs).

This is a plain MkDocs hook (mkdocs.yml -> hooks) instead of the
mkdocs-redirects plugin for two reasons: the plugin does not emit stubs
into the /de/ tree built by mkdocs-static-i18n, and its 1.2.3 release on
PyPI was republished under the ProperDocs fork with an injected
dependency — a supply-chain surface this 30-liner avoids entirely.

Keys are site-relative stub file paths (write locale variants explicitly —
only for URLs that actually existed in that locale). Values are the
root-absolute target URLs (the site is served at the domain root).
"""

import logging
import os

log = logging.getLogger("mkdocs.hooks.redirects")

# 2026-08: V.connect uplift — Products/V.connect/* -> V.connect/*.
# url-builder existed only in the /de/ tree; the presentation deck only in
# the default tree. Their stubs mirror exactly that.
STUBS = {
    "Products/V.connect/index.html": "/V.connect/",
    "Products/V.connect/Fremdaufruf/overview/index.html": "/V.connect/Fremdaufruf/overview/",
    "Products/V.connect/Fremdaufruf/solution-outline/index.html": "/V.connect/Fremdaufruf/solution-outline/",
    "Products/V.connect/Fremdaufruf/presentation/index.html": "/V.connect/Fremdaufruf/presentation/index.html",
    "de/Products/V.connect/index.html": "/de/V.connect/",
    "de/Products/V.connect/Fremdaufruf/overview/index.html": "/de/V.connect/Fremdaufruf/overview/",
    "de/Products/V.connect/Fremdaufruf/solution-outline/index.html": "/de/V.connect/Fremdaufruf/solution-outline/",
    "de/Products/V.connect/Fremdaufruf/url-builder/index.html": "/de/V.connect/Fremdaufruf/url-builder/",
}

# The marker lets the hook recognize its own output: on_post_build runs
# once per language build under mkdocs-static-i18n, so the second pass
# encounters the first pass's stubs.
MARKER = "<!-- redirect-stub: scripts/hooks/redirects.py -->"

TEMPLATE = """<!doctype html>
""" + MARKER + """
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Redirecting...</title>
    <link rel="canonical" href="{url}">
    <script>location.replace("{url}" + location.hash)</script>
    <meta http-equiv="refresh" content="0; url={url}">
</head>
<body>
You're being redirected to a <a href="{url}">new destination</a>.
</body>
</html>
"""


def on_post_build(config, **kwargs):
    site_dir = config["site_dir"]
    for stub, url in STUBS.items():
        path = os.path.join(site_dir, *stub.split("/"))
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                if MARKER not in f.read(2048):
                    log.warning("redirect stub %s collides with an existing page — skipped", stub)
                    continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(TEMPLATE.format(url=url))
    log.info("redirect stubs written (%d)", len(STUBS))
