"""Batch generate HD images for all published breeds.

Pipeline per breed:
  Stage 1: generate 4 images via fal.ai -> upload to Shopify Files -> record CDN URLs
  Stage 2: update breed JSONs (hero + body wikimedia/wikipedia URL replacements)
  Stage 3: push `generate.py --update` for each chunk of breeds (live Shopify update)

State persisted to batch_state.json so the run can resume after interruption.

Usage:
  python scripts/batch_generate.py --stage stage1
  python scripts/batch_generate.py --stage stage1 --breeds golden-retriever,labrador-retriever
  python scripts/batch_generate.py --stage stage2_3
  python scripts/batch_generate.py --stage stage2_3 --chunk-size 20
  python scripts/batch_generate.py --status
  python scripts/batch_generate.py --spotcheck 5
"""

import argparse
import json
import random
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi  # type: ignore  # noqa: E402
import shopify_files_upload as sfu  # type: ignore  # noqa: E402

TRAITS_PATH = ROOT / "breed_traits.json"
STATE_PATH = ROOT / "batch_state.json"
BREED_DATA_DIR = ROOT / "breed-data"
SAMPLE_IMG_DIR = ROOT / "sample-images"
PUB_LOG_PATH = ROOT / "published_log.json"

LABEL_ADULT = "01-adult-portrait"
LABEL_GROOMING = "02-grooming"
LABEL_LIFESTYLE = "03-lifestyle"
LABEL_PUPPY = "04-puppy"

HERO_LABEL_BY_SUFFIX: dict[str, str] = {
    "":                  LABEL_ADULT,
    "-grooming-guide":   LABEL_GROOMING,
    "-first-year-costs": LABEL_LIFESTYLE,
    "-puppy-checklist":  LABEL_PUPPY,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_traits() -> list[dict]:
    return json.loads(TRAITS_PATH.read_text(encoding="utf-8"))


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def build_prompts_from_trait(t: dict) -> list[tuple[str, str]]:
    return gbi.build_prompts(t["name"], t["coat"], t["grooming_action"], t["puppy_coat"])


# ──────────────────────────────────────────────────────────────────────────
# Stage 1 — generate 4 images per breed and upload each to Shopify Files
# ──────────────────────────────────────────────────────────────────────────


def stage1_one_breed(fal_key: str, store: str, token: str, trait: dict, state: dict) -> None:
    slug = trait["slug"]
    out_dir = SAMPLE_IMG_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    prev = state.get(slug, {})
    image_urls: dict[str, str] = dict(prev.get("image_urls", {}))
    prompts = build_prompts_from_trait(trait)

    to_generate = [(label, prompt) for label, prompt in prompts if label not in image_urls]
    if to_generate:
        print(f"  generating {len(to_generate)} images for {slug}...", flush=True)
        local_paths: dict[str, Path] = {}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(gbi.run_one, fal_key, label, prompt, out_dir): label
                       for label, prompt in to_generate}
            for fut in as_completed(futures):
                label = futures[fut]
                local_paths[label] = fut.result()

        for label, path in local_paths.items():
            print(f"  uploading {label} to Shopify Files...", flush=True)
            url = sfu.upload_one(store, token, path, alt=f"{trait['name']} — {label}")
            image_urls[label] = url
    else:
        print(f"  {slug}: all 4 images already uploaded; skipping", flush=True)

    state[slug] = {
        **prev,
        "image_urls": image_urls,
        "stage1_at": prev.get("stage1_at") or now_iso(),
    }
    save_state(state)


def stage1(traits: list[dict], filter_slugs: set[str] | None) -> None:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store, token = env.get("SHOPIFY_STORE", ""), env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")

    state = load_state()
    targets = traits if not filter_slugs else [t for t in traits if t["slug"] in filter_slugs]
    total = len(targets)
    started = time.time()

    for i, trait in enumerate(targets, 1):
        slug = trait["slug"]
        print(f"\n[{i}/{total}] {slug}", flush=True)
        try:
            stage1_one_breed(fal_key, store, token, trait, state)
            elapsed = time.time() - started
            avg = elapsed / i
            eta = avg * (total - i)
            print(f"  ok ({elapsed:.0f}s elapsed, ~{eta:.0f}s ETA)", flush=True)
        except Exception as e:
            print(f"  FAIL {slug}: {e}", flush=True)
            save_state(state)


# ──────────────────────────────────────────────────────────────────────────
# Stage 2 — patch breed JSONs (hero + body image replacement)
# ──────────────────────────────────────────────────────────────────────────


def pick_body_replacement(old_url: str) -> str:
    fname = old_url.lower()
    if any(k in fname for k in ["puppy", "_pup", "pup_", "young", "juvenile"]):
        return LABEL_PUPPY
    if any(k in fname for k in ["running", "playing", "fetch", "active", "park", "field"]):
        return LABEL_LIFESTYLE
    if any(k in fname for k in ["groom", "bath", "brush"]):
        return LABEL_GROOMING
    return LABEL_ADULT


URL_REGEX = re.compile(r"https?://[^\s\"'<>)\]]+\.(?:jpe?g|png|gif|webp)", re.IGNORECASE)


def patch_html(html: str, image_urls: dict[str, str]) -> tuple[str, int]:
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        old = m.group(0)
        if "cdn.shopify.com" in old:
            return old
        label = pick_body_replacement(old)
        new = image_urls.get(label) or image_urls.get(LABEL_ADULT) or old
        if new != old:
            count += 1
        return new

    return URL_REGEX.sub(repl, html), count


def patch_breed_jsons(slug: str, image_urls: dict[str, str]) -> dict:
    stats = {"hero_updated": 0, "body_replacements": 0}

    for suffix, label in HERO_LABEL_BY_SUFFIX.items():
        target_slug = slug + suffix
        path = BREED_DATA_DIR / f"{target_slug}.json"
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))

        new_hero = image_urls.get(label) or image_urls.get(LABEL_ADULT)
        if new_hero:
            images = d.setdefault("images", {})
            hero = images.setdefault("hero", {})
            if hero.get("url") != new_hero:
                hero["url"] = new_hero
                stats["hero_updated"] += 1

        sections = d.get("sections", {})
        if isinstance(sections, dict):
            for sec_val in sections.values():
                if isinstance(sec_val, dict) and isinstance(sec_val.get("html"), str):
                    new_html, n = patch_html(sec_val["html"], image_urls)
                    if n:
                        sec_val["html"] = new_html
                        stats["body_replacements"] += n

        # images.secondary[] — non-Shopify body image URLs replaced via filename heuristic
        secondary = images.get("secondary") if isinstance(images, dict) else None
        if isinstance(secondary, list):
            for entry in secondary:
                if isinstance(entry, dict):
                    old = entry.get("url", "")
                    if old and "cdn.shopify.com" not in old:
                        pick = pick_body_replacement(old)
                        new = image_urls.get(pick) or image_urls.get(LABEL_ADULT)
                        if new and new != old:
                            entry["url"] = new
                            stats["body_replacements"] += 1

        path.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def stage2(filter_slugs: set[str] | None) -> None:
    state = load_state()
    targets = [s for s in state if state[s].get("stage1_at") and not state[s].get("stage2_at")]
    if filter_slugs is not None:
        targets = [s for s in targets if s in filter_slugs]
    print(f"stage 2: patching JSONs for {len(targets)} breeds")
    for i, slug in enumerate(targets, 1):
        st = state[slug]
        stats = patch_breed_jsons(slug, st["image_urls"])
        st["stage2_at"] = now_iso()
        st["stage2_stats"] = stats
        save_state(state)
        print(f"  [{i}/{len(targets)}] {slug}: hero={stats['hero_updated']} body={stats['body_replacements']}")


# ──────────────────────────────────────────────────────────────────────────
# Stage 3 — push `generate.py --update` in chunks
# ──────────────────────────────────────────────────────────────────────────


def stage3(filter_slugs: set[str] | None, chunk_size: int) -> None:
    state = load_state()
    pub = json.loads(PUB_LOG_PATH.read_text(encoding="utf-8")) if PUB_LOG_PATH.exists() else {}
    candidates = [s for s in state if state[s].get("stage2_at") and not state[s].get("stage3_at")]
    if filter_slugs is not None:
        candidates = [s for s in candidates if s in filter_slugs]

    all_slugs: list[str] = []
    for s in candidates:
        for suffix in HERO_LABEL_BY_SUFFIX.keys():
            target = s + suffix
            if (BREED_DATA_DIR / f"{target}.json").exists() and target in pub:
                all_slugs.append(target)

    print(f"stage 3: pushing {len(all_slugs)} live articles in chunks of {chunk_size}")
    pushed_breeds: set[str] = set()
    for i in range(0, len(all_slugs), chunk_size):
        chunk = all_slugs[i:i + chunk_size]
        print(f"\n--- chunk {i // chunk_size + 1}: {len(chunk)} articles ---")
        cmd = ["python", str(ROOT / "scripts" / "generate.py"), *chunk, "--update"]
        proc = subprocess.run(cmd, input="YES\n", text=True, cwd=str(ROOT))
        if proc.returncode != 0:
            print(f"chunk failed (exit={proc.returncode}); state preserved, you can retry")
            return
        for s in chunk:
            base = s
            for suffix in HERO_LABEL_BY_SUFFIX.keys():
                if suffix and s.endswith(suffix):
                    base = s[: -len(suffix)]
                    break
            pushed_breeds.add(base)

    now = now_iso()
    for s in pushed_breeds:
        if s in state:
            state[s]["stage3_at"] = now
    save_state(state)
    print(f"\nstage 3 done: {len(pushed_breeds)} breeds marked stage3_at")


# ──────────────────────────────────────────────────────────────────────────
# Status / spotcheck helpers
# ──────────────────────────────────────────────────────────────────────────


def status() -> None:
    state = load_state()
    s1 = sum(1 for v in state.values() if v.get("stage1_at"))
    s2 = sum(1 for v in state.values() if v.get("stage2_at"))
    s3 = sum(1 for v in state.values() if v.get("stage3_at"))
    print(f"breeds with state: {len(state)}")
    print(f"  stage1 (generated+uploaded): {s1}")
    print(f"  stage2 (json patched):       {s2}")
    print(f"  stage3 (live pushed):        {s3}")


def spotcheck(n: int) -> None:
    state = load_state()
    done = [s for s in state if state[s].get("image_urls", {}) and len(state[s]["image_urls"]) >= 4]
    if not done:
        print("no fully-uploaded breeds available for spotcheck")
        return
    n = min(n, len(done))
    random.seed(int(time.time()))
    sample = random.sample(done, n)
    print(f"\n=== spotcheck: {n} random breeds ===\n")
    for slug in sample:
        urls = state[slug]["image_urls"]
        print(f"--- {slug} ---")
        for label in [LABEL_ADULT, LABEL_GROOMING, LABEL_LIFESTYLE, LABEL_PUPPY]:
            print(f"  {label}: {urls.get(label, '???')}")
        print()


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["stage1", "stage2", "stage3", "stage2_3"])
    ap.add_argument("--breeds", help="comma-separated slugs to filter")
    ap.add_argument("--chunk-size", type=int, default=20)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--spotcheck", type=int, metavar="N")
    args = ap.parse_args()

    if args.status:
        status(); return 0
    if args.spotcheck is not None:
        spotcheck(args.spotcheck); return 0

    traits = load_traits()
    filter_slugs = set(args.breeds.split(",")) if args.breeds else None

    if args.stage == "stage1":
        stage1(traits, filter_slugs)
    elif args.stage == "stage2":
        stage2(filter_slugs)
    elif args.stage == "stage3":
        stage3(filter_slugs, args.chunk_size)
    elif args.stage == "stage2_3":
        stage2(filter_slugs)
        stage3(filter_slugs, args.chunk_size)
    else:
        ap.print_help()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
