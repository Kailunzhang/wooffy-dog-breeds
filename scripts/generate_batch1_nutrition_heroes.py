"""Batch-generate HD heroes for 10 new 'Can Dogs Eat X' articles
(Batch 1 series): chocolate, grapes, onions, peanut butter, bananas,
apples, rice, watermelon, strawberries, eggs.

Same pattern as scripts/generate_nutrition_heroes_batch.py. Each food
gets a still-life food photograph hero rather than a dog-with-food
shot (the toxic ones especially should not feature a dog).

Sequential to respect fal.ai concurrency. After running, run:
    echo YES | python3 scripts/generate.py <10 slugs> --publish

One-shot run:
    python3 scripts/generate_batch1_nutrition_heroes.py
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

OUT_DIR = ROOT / "sample-images" / "nutrition-heroes"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "soft natural daylight, warm tones, magazine-quality food "
    "photography, photorealistic, no humans, no text, no dogs"
)


TARGETS: list[tuple[str, str, str]] = [
    ("can-dogs-eat-chocolate",
     "A still-life photograph of dark chocolate bars and cocoa powder "
     "on a wooden kitchen counter beside a small ceramic dog bowl",
     "Dark chocolate bars displayed with a warning symbol — chocolate is "
     "toxic to dogs and should never be fed as a treat"),
    ("can-dogs-eat-grapes",
     "A still-life food photograph of fresh red and green grape bunches "
     "on a wooden cutting board beside a small ceramic dog bowl",
     "Bunches of fresh red and green grapes — grapes are toxic to dogs "
     "and should never be fed as a treat"),
    ("can-dogs-eat-onions",
     "A still-life food photograph of whole yellow onions, sliced red "
     "onion, and green scallions on a wooden cutting board",
     "Whole and sliced raw onions on a wooden cutting board — onions and "
     "all Allium-family plants are toxic to dogs"),
    ("can-dogs-eat-peanut-butter",
     "A still-life food photograph of an open jar of natural peanut "
     "butter and a small ceramic dog bowl on a wooden kitchen counter",
     "An open jar of natural peanut butter beside a small ceramic dog "
     "bowl on a wooden kitchen counter — plain peanut butter is safe for "
     "dogs when xylitol-free"),
    ("can-dogs-eat-bananas",
     "A still-life food photograph of a bunch of fresh ripe yellow "
     "bananas on a wooden cutting board beside a small ceramic dog bowl",
     "A bunch of fresh yellow bananas beside a small ceramic dog bowl on "
     "a wooden kitchen counter — bananas are safe and nutritious for "
     "dogs in moderation"),
    ("can-dogs-eat-apples",
     "A still-life food photograph of fresh red and green apples whole "
     "and sliced on a wooden cutting board beside a small ceramic dog bowl",
     "Fresh red and green apples on a wooden cutting board beside a "
     "small ceramic dog bowl — apples are safe for dogs once seeds and "
     "core are removed"),
    ("can-dogs-eat-rice",
     "A still-life food photograph of cooked plain white rice in a small "
     "white ceramic bowl on a wooden kitchen counter beside a small dog bowl",
     "Cooked plain white rice in a small bowl on a wooden kitchen "
     "counter — plain rice is a veterinary bland-diet staple for dogs"),
    ("can-dogs-eat-watermelon",
     "A still-life food photograph of fresh sliced red watermelon on a "
     "wooden cutting board beside a small ceramic dog bowl",
     "Sliced red watermelon on a wooden cutting board beside a small "
     "ceramic dog bowl — watermelon is a safe hydrating treat for dogs "
     "once seeded and de-rinded"),
    ("can-dogs-eat-strawberries",
     "A still-life food photograph of fresh ripe red strawberries in a "
     "small wicker basket on a wooden kitchen counter beside a small "
     "ceramic dog bowl",
     "Fresh red strawberries with green tops in a wicker basket beside a "
     "small ceramic dog bowl — strawberries are safe and beneficial for "
     "dogs in moderation"),
    ("can-dogs-eat-eggs",
     "A still-life food photograph of scrambled eggs on a small white "
     "plate beside a ceramic dog bowl on a wooden kitchen counter",
     "Cooked scrambled eggs on a small plate beside a ceramic dog bowl "
     "on a wooden kitchen counter — cooked eggs are a safe and "
     "nutrient-dense food for dogs"),
]


def build_prompt(specific: str) -> str:
    return f"{specific}, {STYLE_TAIL}"


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
    for slug, specific, alt_text in TARGETS:
        json_path = BREED_DATA / f"{slug}.json"
        if not json_path.exists():
            print(f"[{slug}] SKIP: no JSON")
            results.append((slug, None, "no-json"))
            continue
        try:
            print(f"\n>>> [{slug}] generating hero via fal.ai...")
            prompt = build_prompt(specific)
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
        print(f"\nNext: echo YES | python3 scripts/generate.py {slugs} --publish")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
