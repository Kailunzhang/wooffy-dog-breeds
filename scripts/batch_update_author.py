"""Batch-update the author field on every Shopify blog article to Kailun Zhang.

Fixes the E-E-A-T problem identified in the SEO audit where the JSON-LD schema
showed author = "Shopify API" across all 727 articles.

Strategy:
  1. Paginate /admin/api/2024-01/blogs/{id}/articles.json to enumerate all articles
  2. For each article, PUT {article: {id, author: "Kailun Zhang"}}
  3. Parallel via ThreadPoolExecutor (default 4 workers) to stay under Shopify rate limits (2 req/s)
  4. Skip articles that already have the correct author

Usage: python3 scripts/batch_update_author.py [--dry-run] [--workers N]
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

NEW_AUTHOR = "Kailun Zhang"
API_VERSION = "2024-01"


def load_env() -> dict[str, str]:
    env_path = ROOT / ".env"
    out: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
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
    """Paginate through all articles in the blog (handles >250 via Link header)."""
    all_arts: list[dict] = []
    next_url: str | None = (
        f"https://{store}/admin/api/{API_VERSION}/blogs/{blog_id}/articles.json"
        f"?limit=250&fields=id,handle,author,title"
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


def update_author(store: str, token: str, blog_id: str, article: dict) -> tuple[int, str, bool]:
    aid = article["id"]
    if article.get("author") == NEW_AUTHOR:
        return aid, article["handle"], False
    url = f"https://{store}/admin/api/{API_VERSION}/blogs/{blog_id}/articles/{aid}.json"
    payload = {"article": {"id": aid, "author": NEW_AUTHOR}}
    try:
        http_json("PUT", url, token, payload)
        return aid, article["handle"], True
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(2)
            http_json("PUT", url, token, payload)
            return aid, article["handle"], True
        raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    env = load_env()
    store, token, blog_id = env["SHOPIFY_STORE"], env["SHOPIFY_TOKEN"], env["SHOPIFY_BLOG_ID"]

    print(f"Enumerating all articles in blog {blog_id}...")
    arts = list_all_articles(store, token, blog_id)
    print(f"\nTotal articles found: {len(arts)}")
    needs_update = [a for a in arts if a.get("author") != NEW_AUTHOR]
    already_ok = len(arts) - len(needs_update)
    print(f"  already correct: {already_ok}")
    print(f"  need update:     {len(needs_update)}")

    if args.dry_run or not needs_update:
        print("\n(dry-run or nothing to do)")
        return 0

    print(f"\nUpdating {len(needs_update)} articles (workers={args.workers})...")
    started = time.time()
    updated, skipped, failed = 0, 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(update_author, store, token, blog_id, a): a for a in needs_update}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                aid, handle, did_update = fut.result()
                if did_update:
                    updated += 1
                else:
                    skipped += 1
            except Exception as e:
                failed += 1
                print(f"  FAIL: {e}", flush=True)
            if i % 50 == 0 or i == len(needs_update):
                elapsed = time.time() - started
                rate = i / elapsed if elapsed > 0 else 0
                print(f"  progress: {i}/{len(needs_update)} | {rate:.1f} req/s | {elapsed:.0f}s elapsed", flush=True)

    print(f"\nDone. updated={updated}  skipped={skipped}  failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
