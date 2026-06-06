"""Batch-generate HD heroes for 7 nutrition articles whose original
Shopify CDN URLs returned 404, blocking the internal-link push.

Mirrors scripts/generate_quinoa_hero.py: fal.ai Nano Banana Pro ->
Shopify Files upload -> patch breed-data JSON. Run sequentially to
respect fal.ai rate limits.

After this, run:
    echo YES | python3 scripts/generate.py <slugs...> --update

to push the new heroes + Related Reading section to Shopify.

One-shot run:
    python3 scripts/generate_nutrition_heroes_batch.py
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


def build_prompt(food_phrase: str) -> str:
    return (
        f"An adult Golden Retriever sitting calmly on a clean light "
        f"wooden kitchen floor next to a small white ceramic bowl "
        f"containing {food_phrase}, the dog is looking down at the "
        f"bowl with a soft happy expression, warm natural morning "
        f"daylight pouring in through an out-of-focus window in the "
        f"background, "
        f"the dog is the absolute single subject perfectly centered "
        f"in the frame with full body and all four legs visible "
        f"alongside the ceramic bowl, "
        f"soft natural daylight, shallow depth of field with sharp "
        f"focus on the dog and the bowl, professional pet lifestyle "
        f"photography, photorealistic, magazine cover quality, "
        f"no humans, no hands, no text"
    )


# (slug, food_phrase, alt_food, alt_descriptor)
TARGETS: list[tuple[str, str, str, str]] = [
    ("can-dogs-eat-blueberries",
     "fresh ripe blueberries",
     "blueberries",
     "an antioxidant-rich low-calorie treat for dogs"),
    ("can-dogs-eat-butternut-squash-a-nutritious-addition-to-your-dogs-diet",
     "cooked diced butternut squash",
     "cooked butternut squash",
     "a fiber and vitamin A source safe for dogs in moderation"),
    ("can-dogs-eat-chicken-breast",
     "shredded plain cooked chicken breast",
     "cooked chicken breast",
     "a lean protein source for dogs"),
    ("can-dogs-eat-salmon",
     "flaked cooked salmon",
     "cooked salmon",
     "rich in omega-3 fatty acids for dogs' skin and coat"),
    ("can-dogs-have-almond-butter",
     "a small smear of plain almond butter",
     "almond butter",
     "safe in tiny amounts as an occasional treat"),
    ("carrots-for-dogs",
     "fresh whole carrots and a few carrot sticks",
     "carrots",
     "a crunchy low-calorie source of fiber and vitamin A"),
    ("why-pumpkin-is-good-for-dogs",
     "cooked pumpkin puree",
     "pumpkin puree",
     "a digestive aid rich in fiber for dogs"),
]


def patch_json(slug: str, cdn_url: str, alt_text: str) -> tuple[str, str]:
    json_path = BREED_DATA / f"{slug}.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    hero = data.setdefault("images", {}).setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    hero["alt"] = alt_text
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
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
    for slug, food_phrase, alt_food, alt_descriptor in TARGETS:
        json_path = BREED_DATA / f"{slug}.json"
        if not json_path.exists():
            print(f"[{slug}] SKIP: breed-data JSON missing")
            results.append((slug, None, "no-json"))
            continue
        try:
            print(f"\n>>> [{slug}] generating hero via fal.ai...")
            prompt = build_prompt(food_phrase)
            src = gbi.run_one(fal_key, slug, prompt, OUT_DIR)
            unique = OUT_DIR / f"{slug}-hero.png"
            if src != unique:
                if unique.exists():
                    unique.unlink()
                src.rename(unique)

            print(f"[{slug}] uploading to Shopify Files...")
            alt_text = (
                f"Golden Retriever next to a bowl of {alt_food} "
                f"in a sunlit kitchen — {alt_descriptor}"
            )
            cdn_url = sfu.upload_one(store, token, unique, alt=alt_text)
            print(f"[{slug}] CDN URL: {cdn_url}")

            old, new = patch_json(slug, cdn_url, alt_text)
            print(f"[{slug}] patched JSON: {old[:60]}... -> {new[:70]}")
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
        print(f"  {status}  {slug}  {(url or err or '')[:80]}")
    if ok:
        slugs = " ".join(s for s, u, _ in results if u)
        print(f"\nNext: echo YES | python3 scripts/generate.py {slugs} --update")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
