"""Pinterest API automation - bulk-publish pins from PIN_CONFIGS.

Subcommands:
  setup-boards            Create 8 Wooffy boards (or detect existing).
                          Writes pinterest-boards.json with name -> id.
  publish --batch=N       Post N unpublished pins. Updates
                          pinterest-published.json.
  status                  Show how many pins posted / pending.

Env vars (from .env locally, or GitHub Actions secrets):
  PINTEREST_APP_ID
  PINTEREST_APP_SECRET
  PINTEREST_REFRESH_TOKEN
  (Optional) PINTEREST_ACCESS_TOKEN - will be auto-refreshed if expired.

State files:
  pinterest-boards.json     {board_name: board_id}
  pinterest-published.json  {pin_key: {pin_id, posted_at, board_id, title}}

Where pin_key = "<slug>-<variant>" (e.g., "goldendoodle-a").
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from pinterest_pin_copy import PIN_CONFIGS, article_url, load_article  # noqa: E402

ENV_PATH = ROOT / ".env"
BOARDS_PATH = ROOT / "pinterest-boards.json"
PUBLISHED_PATH = ROOT / "pinterest-published.json"

API_BASE = "https://api.pinterest.com/v5"
TOKEN_ENDPOINT = f"{API_BASE}/oauth/token"

BOARDS = [
    ("Dog Breed Guides",
     "Expert breed-by-breed guides covering temperament, care, health, and cost for 158+ dog breeds."),
    ("Best Dogs For...",
     "Roundup guides matching dog breeds to lifestyles - active people, families, hot climates, and more."),
    ("Dog Care & Grooming",
     "Breed-specific grooming routines, brushing techniques, bathing schedules, and coat care."),
    ("Puppy Costs & Budget",
     "Real first-year costs, monthly budgeting, food prices, and money-saving tactics for dog owners."),
    ("Doodle Dogs",
     "Goldendoodle, Labradoodle, Bernedoodle and other doodle hybrids - breed guides and ethical buyer advice."),
    ("Dog Tech & Gear",
     "Smart collars, GPS trackers, modern dog houses, and the tech that improves life with a dog."),
    ("Dog Health",
     "Tick prevention, brachycephalic care, common breed health risks, and when to call the vet."),
    ("Seasonal Dog Care",
     "Summer cooling for double-coated breeds, winter paw protection, and year-round seasonal dog care."),
]


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for k, v in os.environ.items():
        if k.startswith("PINTEREST_"):
            env[k] = v
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env


def refresh_access_token(app_id: str, app_secret: str, refresh_token: str) -> str:
    basic = base64.b64encode(f"{app_id}:{app_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_ENDPOINT,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        timeout=30,
    )
    if resp.status_code != 200:
        sys.exit(f"Refresh-token call failed (HTTP {resp.status_code}): {resp.text}")
    return resp.json()["access_token"]


def get_access_token(env: dict[str, str]) -> str:
    refresh_token = env.get("PINTEREST_REFRESH_TOKEN")
    app_id = env.get("PINTEREST_APP_ID")
    app_secret = env.get("PINTEREST_APP_SECRET")
    if not (refresh_token and app_id and app_secret):
        sys.exit("Missing PINTEREST_APP_ID / PINTEREST_APP_SECRET / PINTEREST_REFRESH_TOKEN. Run pinterest_oauth_setup.py first.")
    return refresh_access_token(app_id, app_secret, refresh_token)


def api(method: str, endpoint: str, token: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers.setdefault("Authorization", f"Bearer {token}")
    headers.setdefault("Content-Type", "application/json")
    url = endpoint if endpoint.startswith("http") else f"{API_BASE}{endpoint}"
    return requests.request(method, url, headers=headers, timeout=30, **kwargs)


def cmd_setup_boards(env: dict[str, str]) -> int:
    token = get_access_token(env)
    print("Listing existing boards...")
    resp = api("GET", "/boards?page_size=100", token)
    if resp.status_code != 200:
        sys.exit(f"GET /boards failed (HTTP {resp.status_code}): {resp.text}")
    existing = {b["name"]: b["id"] for b in resp.json().get("items", [])}
    print(f"  Found {len(existing)} existing boards: {list(existing)}")

    mapping: dict[str, str] = {}
    for name, description in BOARDS:
        if name in existing:
            print(f"  EXISTS    {name!r}  ->  id {existing[name]}")
            mapping[name] = existing[name]
            continue
        print(f"  CREATING  {name!r}")
        r = api("POST", "/boards", token, json={
            "name": name,
            "description": description,
            "privacy": "PUBLIC",
        })
        if r.status_code != 201:
            print(f"    ERROR (HTTP {r.status_code}): {r.text}", file=sys.stderr)
            continue
        mapping[name] = r.json()["id"]
        print(f"    OK  id {mapping[name]}")

    BOARDS_PATH.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(mapping)} board IDs -> {BOARDS_PATH}")
    return 0


def load_boards() -> dict[str, str]:
    if not BOARDS_PATH.exists():
        sys.exit("pinterest-boards.json not found. Run: python3 scripts/pinterest_api.py setup-boards")
    return json.loads(BOARDS_PATH.read_text(encoding="utf-8"))


def load_published() -> dict[str, dict[str, Any]]:
    if PUBLISHED_PATH.exists():
        return json.loads(PUBLISHED_PATH.read_text(encoding="utf-8"))
    return {}


def save_published(state: dict[str, dict[str, Any]]) -> None:
    PUBLISHED_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def enumerate_pins() -> list[tuple[str, str, dict]]:
    """Return list of (pin_key, slug, variant_cfg) for all 40 planned pins."""
    out: list[tuple[str, str, dict]] = []
    for cfg in PIN_CONFIGS:
        slug = cfg["slug"]
        for variant_key in ("a", "b"):
            pin_key = f"{slug}-{variant_key}"
            out.append((pin_key, slug, cfg[variant_key]))
    return out


def cmd_status(env: dict[str, str]) -> int:
    published = load_published()
    all_pins = enumerate_pins()
    total = len(all_pins)
    posted = sum(1 for k, _, _ in all_pins if k in published)
    pending = total - posted
    print(f"Pins posted:  {posted} / {total}")
    print(f"Pins pending: {pending}")
    print()
    if pending:
        print(f"Next {min(5, pending)} to post:")
        c = 0
        for pin_key, slug, _ in all_pins:
            if pin_key not in published:
                print(f"  {pin_key}")
                c += 1
                if c >= 5:
                    break
    if posted:
        print(f"\nMost-recent {min(3, posted)} posted:")
        items = [(k, v) for k, v in published.items() if v.get("posted_at")]
        items.sort(key=lambda kv: kv[1]["posted_at"], reverse=True)
        for k, v in items[:3]:
            print(f"  {v['posted_at']}  {k}  ->  pin {v.get('pin_id', '?')}")
    return 0


def post_pin(token: str, board_id: str, pin_key: str, slug: str,
             variant_cfg: dict, display_name: str, hero_url: str,
             blog_handle: str) -> dict | None:
    body = {
        "board_id": board_id,
        "title": variant_cfg["title"][:100],
        "description": variant_cfg["description"][:500],
        "link": article_url(slug, blog_handle, variant_cfg["campaign"],
                            pin_key.rsplit("-", 1)[-1]),
        "alt_text": display_name[:500],
        "media_source": {
            "source_type": "image_url",
            "url": hero_url,
        },
    }
    r = api("POST", "/pins", token, json=body)
    if r.status_code == 201:
        return r.json(), None
    err = f"HTTP {r.status_code}: {r.text[:300]}"
    print(f"    ERROR ({err})", file=sys.stderr)
    return None, err


def cmd_publish(env: dict[str, str], batch: int, dry_run: bool) -> int:
    boards = load_boards()
    published = load_published()
    token = "" if dry_run else get_access_token(env)
    all_pins = enumerate_pins()
    pending = [t for t in all_pins if t[0] not in published]
    if not pending:
        print(f"All {len(all_pins)} pins already posted. Nothing to do.")
        return 0
    to_post = pending[:batch]
    print(f"Posting {len(to_post)} of {len(pending)} pending (batch={batch}, dry_run={dry_run})")
    print()

    success = 0
    failed = 0
    trial_blocked = 0
    for pin_key, slug, variant_cfg in to_post:
        loaded = load_article(slug)
        if loaded is None:
            print(f"  SKIP  {pin_key}: cannot load article")
            failed += 1
            continue
        display_name, hero_url, blog_handle = loaded
        board_name = variant_cfg["board"]
        board_id = boards.get(board_name)
        if not board_id:
            print(f"  SKIP  {pin_key}: board {board_name!r} not in pinterest-boards.json (run setup-boards)")
            failed += 1
            continue
        print(f"  POST  {pin_key:55s}  board='{board_name}'")
        if dry_run:
            print(f"    DRY-RUN  would POST: title='{variant_cfg['title'][:60]}...'")
            success += 1
            continue
        result, err = post_pin(token, board_id, pin_key, slug, variant_cfg,
                               display_name, hero_url, blog_handle)
        if result is None:
            if err and '"code":29' in err:
                # Trial-tier apps may not create production pins. This is
                # the expected state while Standard approval is pending -
                # stop probing (every pin would hit the same wall).
                trial_blocked += 1
                break
            failed += 1
            continue
        published[pin_key] = {
            "pin_id": result.get("id", ""),
            "board_id": board_id,
            "board_name": board_name,
            "title": variant_cfg["title"],
            "posted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        save_published(published)
        success += 1
        print(f"    OK  pin_id={result.get('id')}")
        time.sleep(1.0)

    print(f"\nSummary: ok={success}  failed={failed}  trial_blocked={trial_blocked}  "
          f"remaining={len(pending) - success}")
    if trial_blocked and failed == 0:
        print(
            "Standard access still pending - Pinterest Trial tier blocks "
            "production pins (error 29). This run exits clean; the daily "
            "cron doubles as an approval probe and pins will start flowing "
            "automatically once Standard is granted."
        )
        return 0
    return 0 if failed == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Pinterest API automation for Wooffy")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup-boards", help="Create or detect 8 Wooffy boards")
    sub.add_parser("status", help="Show posted / pending counts")
    pub = sub.add_parser("publish", help="Post N unpublished pins")
    pub.add_argument("--batch", type=int, default=6, help="How many pins to post (default 6)")
    pub.add_argument("--dry-run", action="store_true", help="Show what would be posted, don't call API")
    args = parser.parse_args()

    env = load_env()
    if args.cmd == "setup-boards":
        return cmd_setup_boards(env)
    if args.cmd == "status":
        return cmd_status(env)
    if args.cmd == "publish":
        return cmd_publish(env, batch=args.batch, dry_run=args.dry_run)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
