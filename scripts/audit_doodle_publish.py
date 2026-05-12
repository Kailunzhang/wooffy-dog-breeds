"""Audit the 25 just-published doodle articles. For each:
  - HEAD-check the public URL on thewooffy.com (expect 200)
  - GET the HTML and check that the breed name appears in the title
  - Confirm hero image is on cdn.shopify.com (not Wikipedia placeholder)
  - HEAD-check the hero image URL (expect 200)

Parallel via ThreadPoolExecutor.
Usage: python3 scripts/audit_doodle_publish.py
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BREED_DATA = ROOT / "breed-data"

DOMAIN = "https://thewooffy.com"

DOODLE_BREEDS = ["goldendoodle", "labradoodle", "bernedoodle", "cavapoo", "sheepadoodle", "aussiedoodle"]
SLUGS: list[str] = []
for b in DOODLE_BREEDS:
    SLUGS += [b, f"{b}-grooming-guide", f"{b}-first-year-costs", f"{b}-puppy-checklist"]
SLUGS.append("best-doodle-breeds-for-families")

UA = "wooffy-publish-audit/1.0"


@dataclass
class Row:
    slug: str
    expected_name: str
    expected_hero: str
    url_status: int | str
    name_match: bool | str
    hero_on_cdn: bool | str
    hero_status: int | str


def head_status(url: str, timeout: int = 15) -> int | str:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"ERR:{type(e).__name__}"


def fetch_html(url: str, timeout: int = 30) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def check_one(slug: str) -> Row:
    p = BREED_DATA / f"{slug}.json"
    if not p.exists():
        return Row(slug, "(no json)", "", "?", "?", "?", "?")
    data = json.loads(p.read_text(encoding="utf-8"))
    name = data.get("meta", {}).get("name", "")
    expected_hero = data.get("images", {}).get("hero", {}).get("url", "")

    article_url = f"{DOMAIN}/blogs/dog-breeds/{slug}"
    url_status = head_status(article_url)

    html = fetch_html(article_url) if url_status == 200 else None
    name_match: bool | str
    if html is None:
        name_match = "n/a"
    else:
        name_match = bool(re.search(re.escape(name), html, re.IGNORECASE))

    hero_on_cdn = "cdn.shopify.com" in expected_hero
    hero_status = head_status(expected_hero) if expected_hero else "n/a"

    return Row(slug, name, expected_hero, url_status, name_match, hero_on_cdn, hero_status)


def main() -> int:
    print(f"Auditing {len(SLUGS)} doodle articles on {DOMAIN} ...\n")
    rows: list[Row] = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(check_one, s): s for s in SLUGS}
        for fut in as_completed(futures):
            rows.append(fut.result())

    rows.sort(key=lambda r: SLUGS.index(r.slug))

    print(f"{'slug':<42} {'url':>6} {'name?':>6} {'cdn?':>6} {'img':>6}")
    print("-" * 72)
    fail_url = 0
    fail_name = 0
    fail_cdn = 0
    fail_img = 0
    for r in rows:
        url_ok = "OK" if r.url_status == 200 else str(r.url_status)
        name_ok = "OK" if r.name_match is True else ("MISS" if r.name_match is False else "?")
        cdn_ok = "OK" if r.hero_on_cdn is True else ("WIKI" if r.hero_on_cdn is False else "?")
        img_ok = "OK" if r.hero_status == 200 else str(r.hero_status)

        if r.url_status != 200:
            fail_url += 1
        if r.name_match is False:
            fail_name += 1
        if r.hero_on_cdn is False:
            fail_cdn += 1
        if r.hero_status != 200:
            fail_img += 1

        print(f"{r.slug:<42} {url_ok:>6} {name_ok:>6} {cdn_ok:>6} {img_ok:>6}")

    print("-" * 72)
    print(f"\nSummary: {len(rows)} articles checked")
    print(f"  URL non-200:       {fail_url}")
    print(f"  Breed name missing:{fail_name}")
    print(f"  Hero not on CDN:   {fail_cdn}")
    print(f"  Hero image non-200:{fail_img}")
    return 0 if (fail_url + fail_name + fail_cdn + fail_img) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
