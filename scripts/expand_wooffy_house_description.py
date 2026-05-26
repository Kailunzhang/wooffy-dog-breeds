"""One-off: append SEO-friendly content sections to the wooffy-house-circla
product description. Audit task B / #2 — give the product page enough
substance for Google to rank it for "modern dog house" in regular web SERP
(currently it only ranks in Google Shopping; the homepage is taking the
position-8 web slot because the product description is one short paragraph).

Idempotent: detects whether the appendix has already been applied (via the
heading marker) and no-ops on re-run.

Usage:
    python3 scripts/expand_wooffy_house_description.py           # dry-run
    python3 scripts/expand_wooffy_house_description.py --apply   # PUT to Shopify

Only uses claims already attested elsewhere on the site (roundup article,
launch article, current product description): Scandinavian wooden
construction, 4 sizes (S/M/I/L), interchangeable transparent + bamboo
mesh side panels, handmade rattan storage, easy single-tool assembly,
custom nameplate option.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parent.parent
ENV_PATH: Path = ROOT / ".env"
API_VERSION = "2024-01"
PRODUCT_ID = "7698520571958"  # wooffy-house-circla

# Marker that uniquely identifies the appendix in any future fetch (used
# for idempotency check).
APPENDIX_MARKER = "<h2>Why a Modern Dog House?</h2>"

APPENDIX_HTML = (
    "\n"
    "<h2>Why a Modern Dog House?</h2>\n"
    "<p>Traditional dog crates clash with modern home interiors. The "
    "Wooffy House solves this with premium wooden construction and "
    "Scandinavian design, plus interchangeable side panels — transparent "
    "acrylic for visibility or bamboo mesh for ventilation — and a "
    "handmade rattan storage base. The result is pet furniture you "
    "display, not hide.</p>\n"
    "<h2>Four Sizes, Customizable Style</h2>\n"
    "<p>Available in Small, Medium, Intermediate, and Large to fit dogs "
    "across breeds and body types. Swap side panels to match your dog's "
    "preference for openness or privacy. A custom nameplate option is "
    "available if you'd like a personalized touch.</p>\n"
    "<h2>What's Included</h2>\n"
    "<ul>\n"
    "<li>Premium wooden frame with Scandinavian design</li>\n"
    "<li>Two interchangeable side panels — transparent acrylic and "
    "bamboo mesh</li>\n"
    "<li>Handmade rattan storage basket beneath</li>\n"
    "<li>All hardware and assembly instructions (easy single-tool "
    "assembly)</li>\n"
    "</ul>"
)


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def api(store: str, token: str, method: str, path: str,
        payload: dict | None = None) -> dict:
    url = f"https://{store}/admin/api/{API_VERSION}{path}"
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Shopify-Access-Token", token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Shopify API {e.code} on {url}: {e.read().decode()[:400]}")


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    env = load_env(ENV_PATH)
    store = env.get("SHOPIFY_STORE")
    token = env.get("SHOPIFY_TOKEN")
    if not store or not token:
        sys.exit("SHOPIFY_STORE / SHOPIFY_TOKEN missing in .env")

    mode = "APPLY (will PUT to Shopify)" if apply else "DRY-RUN (no writes)"
    print(f"Mode: {mode}\n")

    data = api(store, token, "GET",
               f"/products/{PRODUCT_ID}.json?fields=id,handle,body_html")
    product = data["product"]
    handle = product["handle"]
    body = product.get("body_html") or ""
    old_len = len(body)

    print(f"[{PRODUCT_ID}] {handle}")
    print(f"  current body length: {old_len} chars")

    if APPENDIX_MARKER in body:
        print("  appendix already present -- no-op (idempotent).")
        return 0

    new_body = body + APPENDIX_HTML
    new_len = len(new_body)
    print(f"  new body length:     {new_len} chars  (+{new_len - old_len})")
    print(f"  appendix preview:\n{APPENDIX_HTML[:200]}...\n")

    if not apply:
        print("Re-run with --apply to push.")
        return 0

    api(store, token, "PUT", f"/products/{PRODUCT_ID}.json",
        {"product": {"id": int(PRODUCT_ID), "body_html": new_body}})
    print("PUSHED to Shopify.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
