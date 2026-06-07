"""Batch-generate HD heroes for 10 new 'Can Dogs Eat X' articles
(Batch 2 series): cheese, yogurt, avocado, broccoli, sweet-potatoes,
tomatoes, pineapple, oranges, bread, raw-meat.

Same pattern as scripts/generate_batch1_nutrition_heroes.py. Each food
gets a still-life food photograph hero (no humans, no dogs, no text).

Sequential to respect fal.ai concurrency. After running, run:
    echo YES | python3 scripts/generate.py <10 slugs> --publish

One-shot run:
    python3 scripts/generate_batch2_nutrition_heroes.py
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
    ("can-dogs-eat-cheese",
     "A still-life food photograph of assorted cheese cubes "
     "(mozzarella, mild cheddar, swiss) on a wooden cutting board "
     "beside a small ceramic dog bowl",
     "Assorted cheese cubes on a wooden board beside a small ceramic "
     "dog bowl — cheese is a safe high-value training treat for most "
     "dogs in moderation"),
    ("can-dogs-eat-yogurt",
     "A still-life food photograph of a small white ceramic bowl of "
     "plain Greek yogurt with a wooden spoon on a wooden kitchen "
     "counter beside a small ceramic dog bowl",
     "A bowl of plain Greek yogurt with a wooden spoon on a kitchen "
     "counter beside a small ceramic dog bowl — plain unsweetened "
     "yogurt is safe for dogs"),
    ("can-dogs-eat-avocado",
     "A still-life food photograph of a halved ripe avocado with the "
     "pit visible on a wooden cutting board beside a small ceramic "
     "dog bowl",
     "A halved ripe avocado showing the pit on a wooden cutting board "
     "beside a small ceramic dog bowl — avocado is not recommended "
     "for dogs because of the pit and high fat content"),
    ("can-dogs-eat-broccoli",
     "A still-life food photograph of fresh green broccoli florets on "
     "a wooden cutting board beside a small ceramic dog bowl",
     "Fresh green broccoli florets on a wooden cutting board beside a "
     "small ceramic dog bowl — broccoli is safe for dogs in small "
     "amounts"),
    ("can-dogs-eat-sweet-potatoes",
     "A still-life food photograph of cooked orange sweet potato "
     "halves on a wooden cutting board beside a small ceramic dog bowl",
     "Cooked sweet potatoes on a wooden cutting board beside a small "
     "ceramic dog bowl — sweet potatoes are safe and nutritious for "
     "dogs when cooked plain"),
    ("can-dogs-eat-tomatoes",
     "A still-life food photograph of fresh ripe red tomatoes (whole "
     "and one sliced) on a wooden cutting board beside a small ceramic "
     "dog bowl",
     "Fresh ripe red tomatoes on a wooden cutting board beside a small "
     "ceramic dog bowl — ripe tomato flesh is safe for dogs in moderation"),
    ("can-dogs-eat-pineapple",
     "A still-life food photograph of fresh sliced ripe pineapple "
     "chunks on a wooden cutting board beside a small ceramic dog bowl",
     "Fresh sliced ripe pineapple on a wooden cutting board beside a "
     "small ceramic dog bowl — fresh pineapple is safe for dogs in "
     "small amounts"),
    ("can-dogs-eat-oranges",
     "A still-life food photograph of a peeled fresh orange with "
     "separated segments on a wooden cutting board beside a small "
     "ceramic dog bowl",
     "Fresh peeled orange segments on a wooden cutting board beside a "
     "small ceramic dog bowl — peeled orange flesh is safe for dogs in "
     "small amounts"),
    ("can-dogs-eat-bread",
     "A still-life food photograph of a sliced loaf of plain baked "
     "white bread on a wooden cutting board beside a small ceramic "
     "dog bowl",
     "Plain sliced baked white bread on a wooden cutting board beside "
     "a small ceramic dog bowl — plain baked bread is safe for dogs in "
     "small amounts"),
    ("can-dogs-eat-raw-meat",
     "A still-life food photograph of fresh raw beef steak cuts on a "
     "wooden cutting board beside a small ceramic dog bowl",
     "Raw beef cuts on a wooden cutting board beside a small ceramic "
     "dog bowl — raw meat feeding is controversial and carries "
     "documented bacterial risks"),
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
