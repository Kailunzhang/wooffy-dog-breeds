"""Generate HD heroes for two articles (2026-09-29):
  - halloween-dog-safety   (hazard article -> objects-only still life, NO dog,
                            per the toxic-food image rule)
  - can-dogs-eat-eggplant  (edible-in-moderation food -> brand style: Golden
                            Retriever next to a white bowl); the live article
                            had lost its hero image.
Same pattern as scripts/generate_seasonal_health_heroes.py.

One-shot run:
    python3 scripts/generate_halloween_eggplant_heroes.py
Then:
    echo YES | python3 scripts/generate.py halloween-dog-safety --publish
    echo YES | python3 scripts/generate.py can-dogs-eat-eggplant --update
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

OUT_DIR = ROOT / "sample-images" / "guide-heroes"
BREED_DATA = ROOT / "breed-data"

TARGETS: list[tuple[str, str, str]] = [
    ("halloween-dog-safety",
     "A moody autumn still life on a rustic wooden table: a wide bowl "
     "overflowing with unbranded wrapped Halloween candy, foil-wrapped "
     "chocolates, lollipops with sticks, a few loose raisins and candy "
     "wrappers, beside a small carved jack-o'-lantern lit by a battery "
     "LED tea light and two coiled glow sticks, warm evening window light, "
     "shallow depth of field, professional food photography, "
     "photorealistic, magazine quality, no dogs, no animals, no people, "
     "no hands, no text, no brand logos",
     "Bowl of wrapped Halloween candy with lollipops, raisins, a carved "
     "jack-o'-lantern and glow sticks — common Halloween hazards for dogs"),
    ("can-dogs-eat-eggplant",
     "An adult Golden Retriever sitting calmly on a clean light wooden "
     "kitchen floor next to a small white ceramic bowl containing plain "
     "cooked diced eggplant, the dog is looking down at the bowl with a "
     "soft happy expression, warm natural morning daylight pouring in "
     "through an out-of-focus window in the background, the dog is the "
     "absolute single subject perfectly centered in the frame with full "
     "body and all four legs visible alongside the ceramic bowl, soft "
     "natural daylight, shallow depth of field with sharp focus on the dog "
     "and the bowl, professional pet lifestyle photography, "
     "photorealistic, magazine cover quality, no humans, no hands, no text",
     "Golden Retriever next to a bowl of plain cooked eggplant in a sunlit "
     "kitchen — safe for most dogs in small, cooked portions"),
]


def patch_json(slug: str, cdn_url: str, alt_text: str) -> str:
    path = BREED_DATA / f"{slug}.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    images = data.get("images")
    if not isinstance(images, dict):
        images = {}
        data["images"] = images
    hero = images.setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    hero["alt"] = alt_text
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)
                    + ("\n" if raw.endswith("\n") else ""),
                    encoding="utf-8", newline="\n")
    return old


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
            old = patch_json(slug, cdn_url, alt_text)
            print(f"[{slug}] CDN URL: {cdn_url}  (was: {old[:60] or '-'})")
        except Exception as e:  # report and continue with the next target
            print(f"[{slug}] ERROR: {e}")
            failed += 1
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
