"""Generate HD heroes for the three senior-dog guides (2026-09-30):
dog-age-in-human-years, arthritis-in-dogs-home-setup, dog-dementia-cognitive-dysfunction.
Same pattern as scripts/generate_buying_guide_heroes.py.

One-shot run:
    python3 scripts/generate_senior_heroes.py
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
STYLE = ("soft natural light, shallow depth of field, professional pet "
         "lifestyle photography, photorealistic, magazine quality, no people, "
         "no hands, no text, no logos")

TARGETS: list[tuple[str, str, str]] = [
    ("dog-age-in-human-years",
     "A calm senior Labrador Retriever with a noticeably white-grey muzzle and "
     "gentle eyes sitting on a light wooden floor in a sunlit living room, "
     "looking softly toward the camera, " + STYLE,
     "Senior Labrador Retriever with a grey muzzle — how dog years translate "
     "into human years depends on size"),
    ("arthritis-in-dogs-home-setup",
     "An older Golden Retriever with a greying face walking carefully along a "
     "long non-slip runner rug laid over a smooth hardwood hallway floor, a "
     "thick supportive orthopedic dog bed visible at the end of the hallway, "
     "warm afternoon light, " + STYLE,
     "Older Golden Retriever walking on a non-slip runner over a hardwood floor "
     "— simple home changes that help dogs with arthritis"),
    ("dog-dementia-cognitive-dysfunction",
     "An elderly small mixed-breed dog with a grey muzzle resting calmly on a "
     "soft bed in a quiet bedroom at night, a small warm night light glowing "
     "near the floor, cozy and safe atmosphere, low-light photography, "
     + STYLE,
     "Elderly dog resting on its bed beside a small night light — a calm night "
     "setup for a dog with cognitive dysfunction"),
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
