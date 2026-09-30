"""Generate HD heroes for the Thanksgiving and Christmas dog-safety guides (2026-09-29).
Hazard articles -> objects-only still life, NO dog (toxic-food image rule).
Same pattern as scripts/generate_halloween_eggplant_heroes.py.

One-shot run:
    python3 scripts/generate_holiday_heroes.py
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

TARGETS: list[tuple[str, str, str]] = [
    ("thanksgiving-dog-safety",
     "A warm Thanksgiving still life on a rustic wooden dining table: a "
     "roasted turkey on a platter with its carcass bones and twine visible, "
     "a bowl of stuffing with visible onions, a gravy boat, a small dish of "
     "raisins, a pumpkin pie and a bowl of mashed potatoes, autumn gourds, "
     "warm late-afternoon window light, shallow depth of field, professional "
     "food photography, photorealistic, magazine quality, no dogs, no "
     "animals, no people, no hands, no text, no brand logos",
     "Thanksgiving table with roast turkey, bones, stuffing with onions, "
     "gravy, raisins and pie — the holiday foods that put dogs at risk"),
    ("christmas-dog-safety",
     "A cozy Christmas still life on a wooden side table beside a decorated "
     "tree: a plate of chocolates and a slice of fruitcake, a poinsettia and "
     "a sprig of holly, a few glass ornaments, loose silver tinsel and "
     "curled gift ribbon, a wrapped present, warm string lights softly out "
     "of focus, evening glow, shallow depth of field, professional "
     "photography, photorealistic, magazine quality, no dogs, no animals, "
     "no people, no hands, no text, no brand logos",
     "Christmas chocolates, fruitcake, poinsettia, holly, tinsel and glass "
     "ornaments — common holiday hazards for dogs"),
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
