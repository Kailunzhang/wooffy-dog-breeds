"""Generate HD heroes for the eight new breed main pages (2026-10-01):
american-pit-bull-terrier, dogo-argentino, rat-terrier, boykin-spaniel,
cockapoo, maltipoo, mini-goldendoodle, mixed-breed-dogs.
Adult dogs, calm and friendly (the two guardian breeds deliberately relaxed,
never menacing). No people, no hands, no text.
Same pattern as scripts/generate_adolescent_heroes.py.

One-shot run:
    python3 scripts/generate_new_breed_heroes.py
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
         "photography, photorealistic, accurate breed anatomy, magazine quality, "
         "no people, no hands, no text, no logos")

TARGETS: list[tuple[str, str, str]] = [
    ("american-pit-bull-terrier",
     "An adult American Pit Bull Terrier with a short glossy fawn coat lying "
     "relaxed on a living room rug, soft friendly eyes, mouth gently open in a "
     "calm happy expression, cozy home interior, " + STYLE,
     "Adult American Pit Bull Terrier relaxing on a living room rug"),
    ("dogo-argentino",
     "An adult all-white Dogo Argentino sitting calmly on a green backyard lawn, "
     "relaxed posture, gentle attentive expression, natural uncropped ears, "
     "late-afternoon light, " + STYLE,
     "Adult white Dogo Argentino sitting calmly on a backyard lawn"),
    ("rat-terrier",
     "An adult tricolor black, white and tan Rat Terrier standing alert in a "
     "garden, ears up, bright curious expression, compact athletic build, "
     + STYLE,
     "Tricolor Rat Terrier standing alert in a garden"),
    ("boykin-spaniel",
     "An adult chocolate-brown Boykin Spaniel with a wavy coat standing at the "
     "grassy edge of a calm lake, wet paws, happy expression, early morning "
     "light, " + STYLE,
     "Chocolate-brown Boykin Spaniel at the edge of a lake"),
    ("cockapoo",
     "An adult apricot Cockapoo with a soft wavy coat sitting on a light-colored "
     "sofa in a bright living room, friendly expression, " + STYLE,
     "Apricot Cockapoo sitting on a sofa in a bright living room"),
    ("maltipoo",
     "An adult cream-white Maltipoo of normal small-dog size resting on a neatly "
     "made bed, fluffy soft coat, dark eyes, calm content expression, " + STYLE,
     "Cream-white Maltipoo resting on a bed"),
    ("mini-goldendoodle",
     "An adult golden Mini Goldendoodle with a wavy curly coat standing in a "
     "sunny park on green grass, happy open-mouth expression, " + STYLE,
     "Golden Mini Goldendoodle standing in a sunny park"),
    ("mixed-breed-dogs",
     "A medium-sized adult brindle mixed-breed dog of no identifiable breed "
     "sitting on a wooden floor in a warm home, soft eyes, relaxed and settled, "
     "an adopted family dog, " + STYLE,
     "Medium-sized brindle mixed-breed dog sitting in a warm home"),
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
