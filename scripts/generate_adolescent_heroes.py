"""Generate HD heroes for the four adolescent-dog guides (2026-10-01):
dog-teenage-phase, how-to-teach-a-dog-recall, leash-reactive-dog,
when-to-spay-or-neuter-a-dog. No people, no hands, no text.
Same pattern as scripts/generate_eol_heroes.py.

One-shot run:
    python3 scripts/generate_adolescent_heroes.py
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
    ("dog-teenage-phase",
     "A lanky nine-month-old yellow Labrador Retriever adolescent with oversized "
     "paws sitting on a living room floor next to a chewed-up cardboard box, head "
     "tilted, playful mischievous expression, " + STYLE,
     "Adolescent Labrador Retriever sitting beside a chewed cardboard box — the "
     "dog teenage phase"),
    ("how-to-teach-a-dog-recall",
     "A young Border Collie mix running joyfully toward the camera across a wide "
     "green park lawn, ears flying, wearing a harness with a long orange training "
     "line trailing behind on the grass, " + STYLE,
     "Young dog running toward the camera on a long training line — practicing "
     "recall"),
    ("leash-reactive-dog",
     "A medium-sized young mixed-breed dog wearing a harness and leash standing "
     "calmly on a quiet tree-lined suburban sidewalk, looking attentively toward "
     "the camera, the leash leading out of frame, " + STYLE,
     "Young mixed-breed dog standing calmly on leash on a quiet sidewalk"),
    ("when-to-spay-or-neuter-a-dog",
     "A healthy young Golden Retriever adolescent sitting calmly on the floor of a "
     "bright, clean, modern veterinary clinic exam room, soft window light, "
     + STYLE,
     "Young Golden Retriever sitting calmly in a bright veterinary exam room"),
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
