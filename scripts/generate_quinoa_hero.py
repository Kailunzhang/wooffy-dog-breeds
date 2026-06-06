"""Generate one HD hero image for can-dogs-eat-quinoa via fal.ai Nano
Banana Pro, upload to Shopify Files, and patch the breed-data JSON.

Mirrors scripts/generate_doodle_roundup_hero.py. The original Shopify
CDN hero was 404; we temporarily swapped to a Wikimedia URL during
today's SEO rewrite. This script puts the brand-consistent HD image
back into place.

One-shot run:
    python3 scripts/generate_quinoa_hero.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi  # noqa: E402
import shopify_files_upload as sfu    # noqa: E402

SLUG = "can-dogs-eat-quinoa"
OUT_DIR = ROOT / "sample-images" / "nutrition-heroes"
BREED_DATA = ROOT / "breed-data"

# Mirrors STYLE_TAIL convention from generate_doodle_roundup_hero.py
# (perfectly centered single subject, lifestyle photography, no humans,
# no text). Specific to the quinoa article: golden retriever +
# ceramic bowl of cooked quinoa, warm kitchen lighting.
PROMPT = (
    "An adult Golden Retriever sitting calmly on a clean light wooden "
    "kitchen floor next to a small white ceramic bowl filled with "
    "cooked fluffy quinoa, the dog is looking down at the bowl with a "
    "soft happy expression, warm natural morning daylight pouring in "
    "through an out-of-focus window in the background, "
    "the dog is the absolute single subject perfectly centered in the "
    "frame with full body and all four legs visible alongside the "
    "ceramic bowl, "
    "soft natural daylight, shallow depth of field with sharp focus "
    "on the dog and the bowl, professional pet lifestyle photography, "
    "photorealistic, magazine cover quality, no humans, no hands, no text"
)


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[{SLUG}] generating hero via fal.ai Nano Banana Pro...")
    src_path = gbi.run_one(fal_key, SLUG, PROMPT, OUT_DIR)

    unique = OUT_DIR / f"{SLUG}-hero.png"
    if src_path != unique:
        if unique.exists():
            unique.unlink()
        src_path.rename(unique)

    print(f"[{SLUG}] uploading to Shopify Files...")
    cdn_url = sfu.upload_one(
        store, token, unique,
        alt=("Golden Retriever next to a bowl of cooked quinoa "
             "in a sunlit kitchen"),
    )
    print(f"[{SLUG}] CDN URL: {cdn_url}")

    json_path = BREED_DATA / f"{SLUG}.json"
    if not json_path.exists():
        print(f"  ERROR: {json_path} not found")
        return 1
    data = json.loads(json_path.read_text(encoding="utf-8"))
    hero = data.setdefault("images", {}).setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    hero["alt"] = (
        "Golden Retriever next to a bowl of cooked quinoa in a "
        "sunlit kitchen — quinoa is safe for dogs in moderation"
    )
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  patched hero in {json_path.name}:")
    print(f"    old: {old[:80]}...")
    print(f"    new: {cdn_url[:80]}")
    print()
    print("Next step:  echo YES | python3 scripts/generate.py "
          f"{SLUG} --update")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
