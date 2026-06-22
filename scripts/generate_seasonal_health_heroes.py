"""Batch-generate HD heroes for 3 high-ROI guide articles
(from scripts/generate_seasonal_health_batch.py):
  - when-is-pavement-too-hot-for-dogs    (paw safety, single dog)
  - dog-tick-prevention-lyme-disease-guide (single dog, tick check)
  - brachycephalic-dogs-boas-buyer-guide  (single brachy dog portrait)

Same pattern as scripts/generate_comparison_batch_v2_heroes.py.

After running:
    echo YES | python3 scripts/generate.py <3 slugs> --update

One-shot run:
    python3 scripts/generate_seasonal_health_heroes.py
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

OUT_DIR = ROOT / "sample-images" / "comparison-hub-heroes"
BREED_DATA = ROOT / "breed-data"

GUIDE_STYLE = (
    "professional pet photography, soft natural daylight, magazine-"
    "quality, photorealistic, no humans visible, no text"
)


TARGETS: list[tuple[str, str, str]] = [
    ("when-is-pavement-too-hot-for-dogs",
     "A mid-size mixed breed dog standing on hot summer pavement in a "
     "suburban neighborhood, bright midday sunlight, asphalt visibly "
     "shimmering from heat, the dog lifting one paw slightly off the "
     "ground, summer outdoor scene, "
     + GUIDE_STYLE,
     "Dog lifting a paw on hot summer pavement — illustrating "
     "paw-burn risk and the 7-second pavement temperature test"),
    ("dog-tick-prevention-lyme-disease-guide",
     "Close-up photograph of a golden retriever's coat being parted by "
     "fingers performing a tick check, the dog calm and relaxed in a "
     "grassy outdoor setting, soft natural light, focus on the coat "
     "and skin inspection, "
     + GUIDE_STYLE.replace("no humans visible, ", ""),
     "Tick check on a Golden Retriever after a summer walk — "
     "daily tick inspection is essential during peak tick season"),
    ("brachycephalic-dogs-boas-buyer-guide",
     "A studio portrait of an adult French Bulldog with characteristic "
     "shortened muzzle and bat ears, sitting calmly on a clean neutral "
     "studio backdrop, soft front lighting that shows the facial "
     "structure clearly, expression alert and engaged, "
     + GUIDE_STYLE,
     "French Bulldog studio portrait — characteristic shortened "
     "brachycephalic facial structure that defines BOAS-prone breeds"),
]


def patch_json(slug: str, cdn_url: str, alt_text: str) -> tuple[str, str]:
    path = BREED_DATA / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    hero = data.setdefault("images", {}).setdefault("hero", {})
    old = hero.get("url", "")
    hero["url"] = cdn_url
    hero["alt"] = alt_text
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8", newline="\n",
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
    for slug, prompt, alt_text in TARGETS:
        json_path = BREED_DATA / f"{slug}.json"
        if not json_path.exists():
            print(f"[{slug}] SKIP: no JSON")
            results.append((slug, None, "no-json"))
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
            print(f"[{slug}] CDN URL: {cdn_url}")
            old, new = patch_json(slug, cdn_url, alt_text)
            print(f"[{slug}] patched JSON")
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
        print(f"  {status}  {slug}")
    if ok:
        slugs = " ".join(s for s, u, _ in results if u)
        print(f"\nNext: echo YES | python3 scripts/generate.py {slugs} --update")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
