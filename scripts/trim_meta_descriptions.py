"""Trim meta_descriptions exceeding 160 chars so they don't get truncated in
Google SERP. Smart trim: keep the longest prefix ending at a sentence
boundary (. ! ?) under 158 chars; fall back to last word boundary + ellipsis.

Two-phase:
  1. Local: update meta.meta_description in breed-data/*.json
  2. Remote: PUT description_tag metafield on each Shopify article

Usage: python3 scripts/trim_meta_descriptions.py [--dry-run] [--workers N]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BD = ROOT / "breed-data"
API_VERSION = "2024-01"
TARGET_MAX = 158


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


def smart_trim(s: str, target: int = TARGET_MAX) -> str:
    """Trim s to <= target chars at a sentence boundary if possible, else word boundary."""
    if len(s) <= target:
        return s
    head = s[:target]
    matches = list(re.finditer(r"[.!?](?=\s|$)", head))
    if matches and matches[-1].end() >= int(target * 0.7):
        return head[: matches[-1].end()].rstrip()
    last_space = head.rfind(" ", 0, target - 1)
    if last_space < 0:
        return head[: target - 1].rstrip() + "..."
    return head[:last_space].rstrip() + "..."


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


def push_description_tag(store: str, token: str, blog_id: str, aid: int, value: str) -> None:
    url = f"https://{store}/admin/api/{API_VERSION}/blogs/{blog_id}/articles/{aid}.json"
    payload = {
        "article": {
            "id": aid,
            "metafields": [
                {
                    "namespace": "global",
                    "key": "description_tag",
                    "value": value,
                    "type": "single_line_text_field",
                }
            ],
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
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    print("Phase 1: Trimming local JSONs...")
    trimmed: dict[str, str] = {}
    for fn in sorted(os.listdir(BD)):
        if not fn.endswith(".json"):
            continue
        p = BD / fn
        d = json.loads(p.read_text(encoding="utf-8"))
        md = d.get("meta", {}).get("meta_description", "") or ""
        if len(md) <= 160:
            continue
        new_md = smart_trim(md)
        if new_md == md:
            continue
        slug = fn[:-5]
        trimmed[slug] = new_md
        if not args.dry_run:
            d["meta"]["meta_description"] = new_md
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  trimmed: {len(trimmed)} files")
    if trimmed:
        sample = list(trimmed.items())[:3]
        for slug, new in sample:
            print(f"  e.g. {slug}: len={len(new)} -> {new[:80]!r}")

    if args.dry_run or not trimmed:
        print("(dry-run or nothing to update)")
        return 0

    print("\nPhase 2: Fetching Shopify article IDs...")
    env = load_env()
    store, token, blog_id = env["SHOPIFY_STORE"], env["SHOPIFY_TOKEN"], env["SHOPIFY_BLOG_ID"]
    arts = list_all_articles(store, token, blog_id)
    handle_to_id = {a["handle"]: a["id"] for a in arts}
    print(f"  fetched {len(arts)} article IDs")

    tasks = [(slug, trimmed[slug], handle_to_id.get(slug)) for slug in trimmed]
    missing = [s for s, _, aid in tasks if aid is None]
    if missing:
        print(f"  WARN: {len(missing)} slugs not found on Shopify (not yet published?):")
        for m in missing[:5]:
            print(f"    {m}")
    tasks = [(s, v, aid) for s, v, aid in tasks if aid is not None]

    print(f"\nPhase 3: Pushing {len(tasks)} description_tag updates (workers={args.workers})...")
    started = time.time()
    updated, failed = 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(push_description_tag, store, token, blog_id, aid, value): slug
            for slug, value, aid in tasks
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
                print(f"  progress: {i}/{len(tasks)} | {rate:.1f} req/s | {elapsed:.0f}s elapsed", flush=True)

    print(f"\nDone. updated={updated}  failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
