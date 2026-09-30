"""Generate HD heroes for the four end-of-life / pet-loss guides (2026-09-30).
Restrained imagery: no visibly sick or distressed dogs, no people, no text.
Same pattern as scripts/generate_senior_heroes.py.

One-shot run:
    python3 scripts/generate_eol_heroes.py
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
STYLE = ("soft warm natural light, calm and gentle mood, shallow depth of field, "
         "professional photography, photorealistic, magazine quality, no people, "
         "no hands, no text, no logos")

TARGETS: list[tuple[str, str, str]] = [
    ("dog-quality-of-life-scale",
     "A peaceful senior dog with a grey muzzle resting comfortably on a soft "
     "knitted blanket on a sofa, eyes half open, a small closed notebook and a "
     "pencil on the blanket nearby, " + STYLE,
     "Senior dog resting on a blanket beside a notebook — tracking good and bad "
     "days with a quality-of-life scale"),
    ("when-to-euthanize-a-dog",
     "A calm elderly dog with a white-grey muzzle lying peacefully on its side on "
     "a thick soft blanket in a quiet sunlit room, relaxed and comfortable, "
     "gentle golden light, " + STYLE,
     "Elderly dog resting peacefully on a soft blanket in warm light"),
    ("coping-with-the-loss-of-a-dog",
     "An empty, well-worn round dog bed by a window with a folded leather collar "
     "and a coiled leash resting on it, soft morning light falling across the "
     "floor, quiet and tender still life, no dogs, no animals, " + STYLE,
     "Empty dog bed by a window with a collar and leash resting on it"),
    ("getting-another-dog-after-loss",
     "A young mixed-breed dog with a soft expression sitting calmly on a rug in "
     "a warm, lived-in living room, afternoon light through the window, relaxed "
     "and settled, " + STYLE,
     "Young dog settling calmly into a warm living room"),
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
