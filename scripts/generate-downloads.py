#!/usr/bin/env python3
"""Generate the Downloads page from Vertama-GmbH/releases via the GitHub API.

Run as a step in publish.yml before mkdocs gh-deploy. Fetches the public
release list, parses each tag in the form <product-slug>-vX.Y.Z[-pre],
groups by product, picks the latest non-prerelease as headliner (falling
back to the latest prerelease if no stable exists yet), and renders the
EN + DE Downloads pages from Jinja2 templates.

The output files (docs/Downloads/index.md, docs/Downloads/index.de.md)
are gitignored — they exist only during a build. To regenerate locally
for `mkdocs serve`, run:

    uv run python scripts/generate-downloads.py

Reads no secrets. Honours $GITHUB_TOKEN if set (lifts the unauthenticated
60-req/hr rate limit to 1000/hr — set automatically inside GitHub
Actions). Jinja2 is used and is transitively available via mkdocs.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

REPO = "Vertama-GmbH/releases"
API_BASE = f"https://api.github.com/repos/{REPO}"

# Per-product metadata. As more products land in Vertama-GmbH/releases,
# add an entry here keyed by the same slug used in the release tag
# (the part before "-vX.Y.Z").
PRODUCTS = {
    "fremdaufruf": {
        "title": "V.connect Fremdaufruf",
        "summary_en": (
            "Local proxy that bridges GET-only KIS workplaces to V.ap "
            "memento endpoints."
        ),
        "summary_de": (
            "Lokaler Proxy, der GET-only-KIS-Arbeitsplätze mit V.ap-"
            "memento-Endpunkten verbindet."
        ),
        "source_repo": "mcp-health/V.connect",
        "source_visibility_en": "private",
        "source_visibility_de": "privat",
        "container_image": "ghcr.io/mcp-health/v.connect/fremdaufruf",
    },
}

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
OUTPUT_DIR = REPO_ROOT / "docs" / "Downloads"

TAG_RE = re.compile(
    r"^(?P<slug>[a-z][a-z0-9-]*)-v(?P<version>[0-9]+\.[0-9]+\.[0-9]+.*)$"
)


def http_get(url: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "vertama-docs-downloads-generator")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_releases() -> list[dict]:
    raw = http_get(f"{API_BASE}/releases?per_page=100")
    return json.loads(raw)


def fetch_releases_until_visible(expected_tag: str) -> list[dict]:
    """Fetch the release list, retrying with backoff until expected_tag
    appears in the response (or a 60-second budget is exhausted). Works
    around the race where the docs publish workflow fires within
    seconds of release creation, while GitHub's list-releases endpoint
    sometimes takes 5–15 seconds to reflect a brand-new release.

    expected_tag is the tag the source-repo release.yml just published
    and is passed through the repository_dispatch client_payload. When
    empty (manual dispatch, push trigger, etc.) the function makes a
    single non-retrying call — there's no specific tag to wait for.
    """
    deadline = time.monotonic() + 60.0
    delay = 2.0
    attempt = 0
    last_releases: list[dict] = []
    while True:
        attempt += 1
        last_releases = fetch_releases()
        if not expected_tag:
            return last_releases
        if any(r.get("tag_name") == expected_tag for r in last_releases):
            if attempt > 1:
                print(
                    f"  expected tag {expected_tag!r} visible on attempt {attempt}",
                    file=sys.stderr,
                )
            return last_releases
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            print(
                f"WARNING: expected tag {expected_tag!r} not visible after "
                f"{attempt} attempts in 60s; proceeding with the last response",
                file=sys.stderr,
            )
            return last_releases
        sleep_for = min(delay, remaining)
        print(
            f"  expected tag {expected_tag!r} not yet visible "
            f"(attempt {attempt}); retrying in {sleep_for:.1f}s…",
            file=sys.stderr,
        )
        time.sleep(sleep_for)
        delay = min(delay * 1.5, 8.0)


def fetch_sha256(asset_url: str) -> str | None:
    """Fetch a .sha256 sidecar and return just the hex hash."""
    try:
        body = http_get(
            asset_url, accept="application/octet-stream"
        ).decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return None
    parts = body.strip().split()
    return parts[0] if parts else None


def parse_tag(tag: str):
    m = TAG_RE.match(tag)
    if not m:
        return None, None
    return m.group("slug"), m.group("version")


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} kB"
    return f"{n / (1024 * 1024):.1f} MB"


def format_date(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def enrich_release(r: dict):
    slug, version = parse_tag(r["tag_name"])
    if not slug:
        return None
    assets = r.get("assets") or []
    zip_asset = next((a for a in assets if a["name"].endswith(".zip")), None)
    exe_asset = next((a for a in assets if a["name"].endswith(".exe")), None)
    return {
        "slug": slug,
        "tag": r["tag_name"],
        "version": version,
        "title": r.get("name") or r["tag_name"],
        "published": format_date(r["published_at"]),
        "prerelease": r["prerelease"],
        "html_url": r["html_url"],
        "assets": assets,
        "zip_asset": zip_asset,
        "exe_asset": exe_asset,
    }


def attach_asset_details(release: dict) -> None:
    """Attach size_human and sha256 to the headliner's primary assets."""
    for key in ("zip_asset", "exe_asset"):
        asset = release.get(key)
        if not asset:
            continue
        asset["size_human"] = format_size(asset["size"])
        sha_sidecar = next(
            (a for a in release["assets"] if a["name"] == asset["name"] + ".sha256"),
            None,
        )
        if sha_sidecar:
            asset["sha256"] = fetch_sha256(sha_sidecar["browser_download_url"])


def build_product_blocks(releases: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in releases:
        enriched = enrich_release(r)
        if enriched:
            grouped[enriched["slug"]].append(enriched)

    blocks = []
    for slug, info in PRODUCTS.items():
        prod_releases = sorted(
            grouped.get(slug, []),
            key=lambda r: r["published"],
            reverse=True,
        )
        stable = [r for r in prod_releases if not r["prerelease"]]
        pre = [r for r in prod_releases if r["prerelease"]]

        if stable:
            headliner = stable[0]
            older_stable = stable[1:]
            pre_list = pre
        elif pre:
            headliner = pre[0]
            older_stable = []
            pre_list = pre[1:]
        else:
            headliner = None
            older_stable = []
            pre_list = []

        if headliner:
            attach_asset_details(headliner)

        blocks.append(
            {
                "slug": slug,
                "info": info,
                "headliner": headliner,
                "older_stable": older_stable,
                "prereleases": pre_list,
            }
        )
    return blocks


def render() -> None:
    expected_tag = os.environ.get("EXPECTED_RELEASE_TAG", "").strip()
    print(f"Fetching releases from {REPO}…", file=sys.stderr)
    if expected_tag:
        print(f"  expecting tag {expected_tag!r} to be present", file=sys.stderr)
    releases = fetch_releases_until_visible(expected_tag)
    print(f"  got {len(releases)} releases", file=sys.stderr)

    blocks = build_product_blocks(releases)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    for lang, out_name in [("en", "index.md"), ("de", "index.de.md")]:
        template = env.get_template(f"downloads_{lang}.md.j2")
        rendered = template.render(products=blocks)
        out_path = OUTPUT_DIR / out_name
        out_path.write_text(rendered, encoding="utf-8")
        print(f"  wrote {out_path.relative_to(REPO_ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    try:
        render()
    except urllib.error.HTTPError as e:
        print(f"GitHub API HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"GitHub API connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)
