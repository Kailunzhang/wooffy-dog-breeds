"""Generate one HD hero image for the doodle roundup, upload to Shopify Files,
and patch best-doodle-breeds-for-families.json with the new CDN URL.

One-shot run: python3 scripts/generate_doodle_roundup_hero.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi
import shopify_files_upload as sfu

SLUG = "best-doodle-breeds-for-families"
OUT_DIR = ROOT / "sample-images" / "roundup-heroes"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "the dog is the absolute single subject perfectly centered with full body and all four legs visible, "
    "soft natural daylight, shallow depth of field with sharp focus on the dog, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

PROMPT = (
    "A friendly cream-and-apricot wavy-coat Goldendoodle sitting on a sunlit grass lawn with a relaxed, "
    "joyful expression, soft teddy-bear face with dark eyes, full body in three-quarter profile showing "
    f"the curly coat texture, warm afternoon golden-hour light, blurred suburban backyard background, {STYLE_TAIL}"
)


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[{SLUG}] generating hero image via fal.ai Nano Banana Pro...")
    src_path = gbi.run_one(fal_key, SLUG, PROMPT, OUT_DIR)

    unique = OUT_DIR / f"roundup-{SLUG}-hero.png"
    if src_path != unique:
        if unique.exists():
            unique.unlink()
        src_path.rename(unique)

    print(f"[{SLUG}] uploading to Shopify Files...")
    cdn_url = sfu.upload_one(store, token, unique, alt=f"{SLUG} hero")
    print(f"[{SLUG}] CDN URL: {cdn_url}")

    json_path = BREED_DATA / f"{SLUG}.json"
    if not json_path.exists():
        print(f"  ERROR: {json_path} not found")
        return 1
    data = json.loads(json_path.read_text(encoding="utf-8"))
    hero = data.setdefault("images", {}).setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  patched hero in {json_path.name}: {old[:60]}... -> {cdn_url[:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
