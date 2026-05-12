"""Batch-set the SEO title_tag metafield on every applicable blog article.

Applies the same template as generate.py:_compute_title_tag - so generate.py
(future articles) and this script (existing articles) stay in sync.

Skips roundup-type articles (they already have descriptive titles).

Usage: python3 scripts/batch_update_title_tags.py [--dry-run] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_VERSION = "2024-01"


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def http_json(method: str, url: str, token: str, body: dict | None = None, timeout: int = 30) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Shopify-Access-Token", token)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def list_all_articles(store: str, token: str, blog_id: str) -> list[dict]:
    all_arts: list[dict] = []
    next_url: str | None = (
        f"https://{store}/admin/api/{API_VERSION}/blogs/{blog_id}/articles.json"
        f"?limit=250&fields=id,handle,title"
    )
    while next_url:
        req = urllib.request.Request(next_url)
        req.add_header("X-Shopify-Access-Token", token)
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            link = r.headers.get("Link", "")
        all_arts.extend(data.get("articles", []))
        next_url = None
        if 'rel="next"' in link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip().strip("<>").strip()
                    break
        print(f"  fetched batch; total so far: {len(all_arts)}", flush=True)
    return all_arts


def compute_title_tag(slug: str, name: str) -> str | None:
    """Mirror of generate.py:_compute_title_tag."""
    roundup_prefixes = ("best-", "most-", "easiest-", "quietest-", "longest-", "rarest-", "low-", "dog-breeds-")
    if any(slug.startswith(p) for p in roundup_prefixes):
        return f"{name}: Top Picks & Care Guide"
    suffix_templates = {
        "-grooming-guide":    "{breed} Grooming Guide: Tools, Tips & Schedule",
        "-first-year-costs":  "{breed} Cost: First-Year & Annual Budget",
        "-puppy-checklist":   "{breed} Puppy Checklist: First 30 Days Essentials",
    }
    for suf, tmpl in suffix_templates.items():
        if slug.endswith(suf):
            base_slug = slug[: -len(suf)]
            breed_display = base_slug.replace("-", " ").title()
            return tmpl.format(breed=breed_display)
    return f"{name} Breed Guide: Cost, Care & Temperament"


def set_title_tag(store: str, token: str, blog_id: str, article: dict, title_tag: str) -> tuple[int, bool]:
    aid = article["id"]
    url = f"https://{store}/admin/api/{API_VERSION}/blogs/{blog_id}/articles/{aid}.json"
    payload = {
        "article": {
            "id": aid,
            "metafields": [
                {
                    "namespace": "global",
                    "key": "title_tag",
                    "value": title_tag,
                    "type": "single_line_text_field",
                }
            ],
        }
    }
    try:
        http_json("PUT", url, token, payload)
        return aid, True
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(3)
            http_json("PUT", url, token, payload)
            return aid, True
        raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    env = load_env()
    store, token, blog_id = env["SHOPIFY_STORE"], env["SHOPIFY_TOKEN"], env["SHOPIFY_BLOG_ID"]

    print(f"Enumerating all articles in blog {blog_id}...")
    arts = list_all_articles(store, token, blog_id)
    print(f"\nTotal articles found: {len(arts)}")

    updates: list[tuple[dict, str]] = []
    roundup_skipped = 0
    for a in arts:
        tt = compute_title_tag(a.get("handle", ""), a.get("title", ""))
        if tt is None:
            roundup_skipped += 1
            continue
        updates.append((a, tt))
    print(f"  roundups skipped:   {roundup_skipped}")
    print(f"  to update:          {len(updates)}")

    if args.dry_run:
        print("\n--- DRY RUN preview (first 10) ---")
        for a, tt in updates[:10]:
            print(f"  {a['handle']:<45} -> {tt}")
        return 0

    if not updates:
        print("nothing to update")
        return 0

    print(f"\nUpdating {len(updates)} articles (workers={args.workers})...")
    started = time.time()
    updated = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(set_title_tag, store, token, blog_id, a, tt): a for a, tt in updates}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
                updated += 1
            except Exception as e:
                failed += 1
                print(f"  FAIL: {e}", flush=True)
            if i % 50 == 0 or i == len(updates):
                elapsed = time.time() - started
                rate = i / elapsed if elapsed > 0 else 0
                print(f"  progress: {i}/{len(updates)} | {rate:.1f} req/s | {elapsed:.0f}s elapsed", flush=True)

    print(f"\nDone. updated={updated}  failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
