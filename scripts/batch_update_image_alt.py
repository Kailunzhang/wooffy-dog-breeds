"""Sweep article.image.alt values on Shopify to match local breed-data/*.json
images.hero.alt - which generate_descriptive_alts.py rewrote with
descriptive, keyword-rich strings.

Idempotent: skips articles whose Shopify alt already equals the local target.

Usage: python3 scripts/batch_update_image_alt.py [--dry-run] [--workers N]
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
BD = ROOT / "breed-data"
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
        f"?limit=250&fields=id,handle,image"
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


def load_local_alt(slug: str) -> tuple[str | None, str | None]:
    p = BD / f"{slug}.json"
    if not p.exists():
        return None, None
    d = json.loads(p.read_text(encoding="utf-8"))
    hero = d.get("images", {}).get("hero", {})
    return hero.get("alt"), hero.get("url")


def push_image_alt(store: str, token: str, blog_id: str, aid: int, src: str, alt: str) -> None:
    url = f"https://{store}/admin/api/{API_VERSION}/blogs/{blog_id}/articles/{aid}.json"
    payload = {
        "article": {
            "id": aid,
            "image": {"src": src, "alt": alt},
        }
    }
    try:
        http_json("PUT", url, token, payload)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(3)
            http_json("PUT", url, token, payload)
        else:
            raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    env = load_env()
    store, token, blog_id = env["SHOPIFY_STORE"], env["SHOPIFY_TOKEN"], env["SHOPIFY_BLOG_ID"]

    print(f"Enumerating articles...")
    arts = list_all_articles(store, token, blog_id)
    print(f"\nTotal: {len(arts)}")

    tasks: list[tuple[int, str, str, str]] = []
    already_ok = 0
    no_local = 0
    no_src = 0
    for a in arts:
        slug = a.get("handle", "")
        new_alt, _ = load_local_alt(slug)
        if not new_alt:
            no_local += 1
            continue
        img = a.get("image") or {}
        current_alt = img.get("alt", "")
        existing_src = img.get("src", "")
        if not existing_src:
            no_src += 1
            continue
        if current_alt == new_alt:
            already_ok += 1
            continue
        tasks.append((a["id"], slug, existing_src, new_alt))

    print(f"  already correct: {already_ok}")
    print(f"  no local JSON:   {no_local}")
    print(f"  no shopify src:  {no_src}")
    print(f"  to update:       {len(tasks)}")

    if args.dry_run:
        print("\n--- DRY RUN preview (first 5) ---")
        for aid, slug, src, alt in tasks[:5]:
            print(f"  {slug}: {alt[:70]!r}")
        return 0

    if not tasks:
        print("nothing to update")
        return 0

    print(f"\nUpdating {len(tasks)} (workers={args.workers})...")
    started = time.time()
    updated, failed = 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(push_image_alt, store, token, blog_id, aid, src, alt): slug
            for aid, slug, src, alt in tasks
        }
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                fut.result()
                updated += 1
            except Exception as e:
                failed += 1
                print(f"  FAIL {futures[fut]}: {e}", flush=True)
            if i % 50 == 0 or i == len(tasks):
                elapsed = time.time() - started
                rate = i / elapsed if elapsed > 0 else 0
                print(f"  progress: {i}/{len(tasks)} | {rate:.1f} req/s | {elapsed:.0f}s", flush=True)

    print(f"\nDone. updated={updated}  failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
