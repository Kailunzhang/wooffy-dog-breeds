"""One-off: rewrite internal links on 4 Shopify articles so they point
to the canonical /products/wooffy-house-circla (instead of variant URLs,
404 slugs, or no link at all). Audit task B — fix the "modern dog house"
cannibalization by transferring link authority to the product page.

Usage:
    python3 scripts/fix_modern_dog_house_links.py           # dry-run, prints diff
    python3 scripts/fix_modern_dog_house_links.py --apply   # actually PUT to Shopify

Each operation asserts the find string appears exactly once in the
fetched body, so we either change the right place or fail loudly with
no half-applied state.
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

PRODUCT_URL = "https://thewooffy.com/products/wooffy-house-circla"

# (article_id, friendly_label, [(find_str, replace_str, op_label), ...])
# Each find_str MUST appear exactly once in the current body. Use the
# curly apostrophe (U+2019) where Shopify's editor inserts it.
OPERATIONS: list[tuple[str, str, list[tuple[str, str, str]]]] = [
    (
        "564654440502",
        "Roundup: top-5-modern-dog-houses-of-2024",
        [
            (
                # Fix the only existing link — currently points to variant Small
                "https://thewooffy.com/products/wooffy-house-circla?variant=43257588056118",
                PRODUCT_URL,
                "fix variant URL on existing 'Wooffy Modern Dog House' link",
            ),
            (
                # Append a CTA paragraph after the last conclusion sentence.
                "Happy shopping, and here's to finding the perfect house for your furry friend!</p>",
                ("Happy shopping, and here's to finding the perfect house for your furry friend!</p>\n"
                 f'<p>Ready to upgrade your dog\'s space? <a href="{PRODUCT_URL}">'
                 "Shop the Wooffy Modern Dog House</a> — minimalist wooden design with "
                 "customizable side panels, 4 sizes from Small to Large.</p>"),
                "append CTA paragraph after conclusion",
            ),
        ],
    ),
    (
        "564596932662",
        "5-benefits-of-owning-an-indoor-dog-kennel",
        [
            (
                # Intro: wrong target (homepage) + wrong anchor text
                '<a href="https://thewooffy.com/">Contemporary Dog Kennel</a>',
                f'<a href="{PRODUCT_URL}">Modern Dog House</a>',
                "fix intro: homepage link -> product, anchor 'Contemporary Dog Kennel' -> 'Modern Dog House'",
            ),
            (
                # Conclusion text link: points to 404 slug wooffy-modern-dog-house
                '<a href="https://thewooffy.com/products/wooffy-modern-dog-house" style="color: #000000;">here</a>',
                f'<a href="{PRODUCT_URL}" style="color: #000000;">the Wooffy Modern Dog House</a>',
                "fix conclusion text link (404 slug -> canonical, 'here' -> meaningful anchor)",
            ),
            (
                # Image link: same 404 slug
                '<a title="Wooffy modern dog house" href="https://thewooffy.com/products/wooffy-modern-dog-house">',
                f'<a title="Wooffy Modern Dog House" href="{PRODUCT_URL}">',
                "fix image link (404 slug -> canonical)",
            ),
        ],
    ),
    (
        "571278753846",
        "wooffy-launches-modern-indoor-dog-crates...",
        [
            (
                "<b>modern indoor dog crates and luxury indoor dog houses</b>",
                f'<b><a href="{PRODUCT_URL}">modern indoor dog crates and luxury indoor dog houses</a></b>',
                "link lead-paragraph keyword phrase",
            ),
            (
                "The result is a <b>modern indoor dog crate</b> that functions",
                f'The result is a <b><a href="{PRODUCT_URL}">modern indoor dog crate</a></b> that functions',
                "link mid-article keyword phrase",
            ),
            (
                "For more information, visit <b>[https://thewooffy.com/]</b>.",
                f'For more information, visit <a href="{PRODUCT_URL}"><b>the Wooffy Modern Dog House collection</b></a>.',
                "fix placeholder URL in footer -> product page",
            ),
        ],
    ),
    (
        "571278917686",
        "redefining-the-indoor-dog-house-as-part-of-the-modern-home",
        [
            # The phrase "Wooffy's indoor dog houses" uses a curly apostrophe (U+2019)
            # in Shopify's editor output.
            (
                "<p data-start=\"1385\" data-end=\"1714\">Wooffy’s indoor dog houses are designed",
                f'<p data-start="1385" data-end="1714"><a href="{PRODUCT_URL}">Wooffy’s indoor dog houses</a> are designed',
                "wrap 'Wooffy's indoor dog houses' as link",
            ),
            (
                # Insert CTA right before the Author: block (unique anchor).
                "<p data-start=\"2225\" data-end=\"2410\">Author",
                (f'<p>Explore the <a href="{PRODUCT_URL}">Wooffy Modern Dog House</a> — '
                 "a wooden indoor dog crate available in four sizes, designed to live "
                 "openly in your home rather than be hidden away.</p>\n"
                 '<p data-start="2225" data-end="2410">Author'),
                "insert CTA paragraph before the Author block",
            ),
        ],
    ),
]


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


def apply_ops(body: str, ops: list[tuple[str, str, str]]) -> tuple[str, list[str]]:
    """Apply ops in order; assert each find is unique. Returns (new_body, log)."""
    log: list[str] = []
    cur = body
    for find_str, replace_str, label in ops:
        n = cur.count(find_str)
        if n != 1:
            raise RuntimeError(
                f"FIND not unique: '{label}' -- got {n} matches "
                f"(want exactly 1). First 80 chars of find: "
                f"{find_str[:80]!r}"
            )
        cur = cur.replace(find_str, replace_str, 1)
        delta = len(replace_str) - len(find_str)
        log.append(f"  OK  [{delta:+5d} chars]  {label}")
    return cur, log


def main(argv: list[str]) -> int:
    apply = "--apply" in argv
    env = load_env(ENV_PATH)
    store = env.get("SHOPIFY_STORE")
    token = env.get("SHOPIFY_TOKEN")
    if not store or not token:
        sys.exit("SHOPIFY_STORE / SHOPIFY_TOKEN missing in .env")

    mode = "APPLY (will PUT to Shopify)" if apply else "DRY-RUN (no writes)"
    print(f"Mode: {mode}\n")

    failures = 0
    for aid, label, ops in OPERATIONS:
        print(f"[{aid}] {label}")
        data = api(store, token, "GET",
                   f"/articles/{aid}.json?fields=id,handle,body_html")
        body = data["article"]["body_html"]
        old_len = len(body)
        try:
            new_body, log = apply_ops(body, ops)
        except RuntimeError as e:
            print(f"  FAIL  {e}")
            failures += 1
            print()
            continue
        for line in log:
            print(line)
        print(f"  body length {old_len} -> {len(new_body)}  "
              f"({len(new_body) - old_len:+d})")
        if apply:
            api(store, token, "PUT", f"/articles/{aid}.json",
                {"article": {"id": int(aid), "body_html": new_body}})
            print("  PUSHED to Shopify.")
        print()

    if failures:
        print(f"FAILED on {failures} article(s). Nothing pushed for those.")
        return 1
    print(f"All {len(OPERATIONS)} articles ready.")
    if not apply:
        print("Re-run with --apply to push.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
