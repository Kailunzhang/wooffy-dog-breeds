"""Generate HD heroes for the three puppy-buying guides (2026-09-30):
puppy-scams, how-to-find-a-responsible-breeder, adopt-or-shop-dog.
Same pattern as scripts/generate_holiday_heroes.py.

One-shot run:
    python3 scripts/generate_buying_guide_heroes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi  # noqa: E402
import shopify_files_upload as sfu    # noqa: E402
from generate_halloween_eggplant_heroes import patch_json  # noqa: E402

OUT_DIR = ROOT / "sample-images" / "guide-heroes"
BREED_DATA = ROOT / "breed-data"
STYLE = ("soft natural daylight, shallow depth of field, professional "
         "lifestyle photography, photorealistic, magazine quality, no people, "
         "no hands, no readable text, no logos")

TARGETS: list[tuple[str, str, str]] = [
    ("puppy-scams",
     "A smartphone lying face-up on a light wooden kitchen table, its screen "
     "showing an adorable fluffy puppy photo in an online listing with a "
     "blurred, unreadable payment button below it, next to a set of house "
     "keys and a closed notebook, " + STYLE,
     "Phone showing an online puppy listing with a payment button — the "
     "set-up behind most puppy scams"),
    ("how-to-find-a-responsible-breeder",
     "A healthy adult Golden Retriever mother lying relaxed on a clean cream "
     "blanket in a bright, tidy home whelping area with five alert "
     "seven-week-old Golden Retriever puppies around her, clean water bowl "
     "nearby, " + STYLE,
     "Golden Retriever mother with her seven-week-old litter in a clean home "
     "setting — what meeting the parents at a responsible breeder looks like"),
    ("adopt-or-shop-dog",
     "A friendly medium-size mixed-breed shelter dog with a short tan coat "
     "sitting in a clean, bright adoption center play room, looking at the "
     "camera with a hopeful, relaxed expression, a soft toy beside it, "
     + STYLE,
     "Friendly mixed-breed dog waiting in a bright adoption center — one side "
     "of the adopt-or-buy decision"),
]


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store, token = env.get("SHOPIFY_STORE", ""), env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failed = 0
    for slug, prompt, alt_text in TARGETS:
        if not (BREED_DATA / f"{slug}.json").exists():
            print(f"[{slug}] SKIP: no JSON")
            failed += 1
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
            patch_json(slug, cdn_url, alt_text)
            print(f"[{slug}] CDN URL: {cdn_url}")
        except Exception as e:  # report and continue with the next target
            print(f"[{slug}] ERROR: {e}")
            failed += 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
