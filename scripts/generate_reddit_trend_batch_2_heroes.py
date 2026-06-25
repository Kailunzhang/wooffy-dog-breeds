"""Batch-generate HD heroes for 3 reddit-trend batch 2 articles:
  - dog-food-on-a-budget-2026
  - smart-dog-collar-buyer-guide-2026
  - doodle-breeding-ethics-2026

Same pattern as scripts/generate_seasonal_health_heroes.py.

After running:
    echo YES | python3 scripts/generate.py <3 slugs> --update
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
    ("dog-food-on-a-budget-2026",
     "A still-life photograph of a stainless steel dog food bowl filled "
     "with dry kibble on a wooden kitchen counter, beside a measuring "
     "cup and a small stack of grocery receipts, soft kitchen lighting, "
     + GUIDE_STYLE,
     "Dog food bowl with kibble beside a measuring cup and receipts — "
     "2026 dog food budget guide"),
    ("smart-dog-collar-buyer-guide-2026",
     "A modern GPS smart dog collar with a small black tracker module "
     "attached to a fabric collar, lying on a clean light wood surface "
     "next to a smartphone showing a map app, top-down view, soft "
     "natural light, "
     + GUIDE_STYLE,
     "Modern GPS smart dog collar beside a smartphone map app — "
     "2026 smart collar buyer guide"),
    ("doodle-breeding-ethics-2026",
     "A studio portrait of two adult Goldendoodles sitting side by side "
     "on a clean neutral backdrop, one apricot-colored and one cream, "
     "calm expressions, soft front lighting that shows their wavy coats, "
     + GUIDE_STYLE,
     "Two adult Goldendoodles in a studio portrait — the doodle "
     "boom and ethical breeding guide for 2026"),
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
