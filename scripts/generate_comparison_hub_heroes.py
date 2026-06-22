"""Batch-generate HD heroes for 4 new articles (commit ab7adc1):
  - siberian-husky-vs-alaskan-malamute     (comparison, side-by-side)
  - french-bulldog-vs-pug                  (comparison, side-by-side)
  - akita-vs-shiba-inu                     (comparison, side-by-side)
  - keep-double-coated-dogs-cool-in-summer (hub, single dog action)

Same pattern as scripts/generate_batch2_nutrition_heroes.py but with
breed-photo prompts (with dogs) instead of still-life food shots.

Sequential to respect fal.ai concurrency. After running, the JSON
files already have the new heroes patched in — push to Shopify with:
    echo YES | python3 scripts/generate.py <4 slugs> --update

One-shot run:
    python3 scripts/generate_comparison_hub_heroes.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi  # noqa: E402
import shopify_files_upload as sfu    # noqa: E402

OUT_DIR = ROOT / "sample-images" / "comparison-hub-heroes"
BREED_DATA = ROOT / "breed-data"

COMPARISON_STYLE = (
    "two adult dogs side by side, full body shots, professional pet "
    "photography, soft natural daylight, clean seamless background, "
    "magazine-quality, photorealistic, no humans, no text"
)
HUB_STYLE = (
    "professional pet photography, soft natural daylight, magazine-"
    "quality, photorealistic, no humans, no text"
)


TARGETS: list[tuple[str, str, str]] = [
    ("siberian-husky-vs-alaskan-malamute",
     "An adult Siberian Husky on the left and an adult Alaskan Malamute "
     "on the right, side by side outdoors on snow, the Husky visibly "
     "smaller and leaner with blue eyes and sickle-curved tail, the "
     "Malamute larger and more muscular with brown eyes and plumed tail, "
     + COMPARISON_STYLE,
     "Siberian Husky and Alaskan Malamute side by side on snow, showing "
     "the size and build difference between the two arctic sled breeds"),
    ("french-bulldog-vs-pug",
     "An adult French Bulldog on the left and an adult fawn Pug on the "
     "right, side by side on a clean studio backdrop, both facing the "
     "camera, the Frenchie visibly larger with bat ears, the Pug smaller "
     "with rose ears and curled tail, "
     + COMPARISON_STYLE,
     "French Bulldog and Pug side by side studio portrait, showing the "
     "size and feature differences between the two brachycephalic "
     "companion breeds"),
    ("akita-vs-shiba-inu",
     "An adult Akita on the left and an adult red Shiba Inu on the "
     "right, side by side outdoors, the Akita visibly much larger and "
     "more powerful with a broad head, the Shiba dramatically smaller "
     "and fox-like, both with prick ears and curled tails, "
     + COMPARISON_STYLE,
     "Akita and Shiba Inu side by side, showing the dramatic size "
     "difference between the two Japanese spitz breeds"),
    ("keep-double-coated-dogs-cool-in-summer",
     "An adult Siberian Husky lying calmly on a blue cooling mat in "
     "the shade of a backyard tree on a hot summer day, beside a "
     "stainless steel water bowl with ice cubes, lush green grass "
     "background, "
     + HUB_STYLE,
     "Siberian Husky resting on a cooling mat in the shade beside a "
     "water bowl with ice — proper summer care for double-coated "
     "northern breeds without shaving the coat"),
]


def build_prompt(specific: str) -> str:
    return specific


def patch_json(slug: str, cdn_url: str, alt_text: str) -> tuple[str, str]:
    path = BREED_DATA / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    hero = data.setdefault("images", {}).setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    hero["alt"] = alt_text
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
    )
    return old, cdn_url


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str | None, str | None]] = []
    for slug, prompt, alt_text in TARGETS:
        json_path = BREED_DATA / f"{slug}.json"
        if not json_path.exists():
            print(f"[{slug}] SKIP: no JSON")
            results.append((slug, None, "no-json"))
            continue
        try:
            print(f"\n>>> [{slug}] generating hero via fal.ai...")
            src = gbi.run_one(fal_key, slug, prompt, OUT_DIR)
            unique = OUT_DIR / f"{slug}-hero.png"
            if src != unique:
                if unique.exists():
                    unique.unlink()
                src.rename(unique)
            print(f"[{slug}] uploading to Shopify Files...")
            cdn_url = sfu.upload_one(store, token, unique, alt=alt_text)
            print(f"[{slug}] CDN URL: {cdn_url}")
            old, new = patch_json(slug, cdn_url, alt_text)
            print(f"[{slug}] patched JSON")
            results.append((slug, cdn_url, None))
        except Exception as e:
            print(f"[{slug}] ERROR: {e}")
            results.append((slug, None, str(e)[:200]))

    print("\n=== summary ===")
    ok = sum(1 for _, u, _ in results if u)
    fail = sum(1 for _, u, _ in results if not u)
    print(f"  ok={ok}  fail={fail}")
    for slug, url, err in results:
        status = "OK  " if url else "FAIL"
        print(f"  {status}  {slug}")
    if ok:
        slugs = " ".join(s for s, u, _ in results if u)
        print(f"\nNext: echo YES | python3 scripts/generate.py {slugs} --update")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
