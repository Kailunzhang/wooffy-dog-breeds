"""Batch-generate HD heroes for the 3 articles from
scripts/generate_comparison_batch_v2.py:
  - labrador-retriever-vs-german-shepherd
  - belgian-malinois-vs-german-shepherd
  - chihuahua-vs-pomeranian

Same pattern as scripts/generate_comparison_hub_heroes.py.

After running:
    echo YES | python3 scripts/generate.py <3 slugs> --update

One-shot run:
    python3 scripts/generate_comparison_batch_v2_heroes.py
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

COMPARISON_STYLE = (
    "two adult dogs side by side, full body shots, professional pet "
    "photography, soft natural daylight, clean seamless background, "
    "magazine-quality, photorealistic, no humans, no text"
)


TARGETS: list[tuple[str, str, str]] = [
    ("labrador-retriever-vs-german-shepherd",
     "An adult yellow Labrador Retriever on the left and an adult "
     "black-and-tan German Shepherd on the right, side by side outdoors "
     "on green grass, both standing alert and facing the camera, "
     "the Lab with friendly relaxed expression and the GSD with "
     "watchful protective expression, "
     + COMPARISON_STYLE,
     "Labrador Retriever and German Shepherd side by side, two of "
     "the most popular American family and working breeds"),
    ("belgian-malinois-vs-german-shepherd",
     "An adult fawn Belgian Malinois on the left and an adult "
     "black-and-tan German Shepherd on the right, side by side outdoors, "
     "both standing alert and facing the camera, the Malinois visibly "
     "leaner and more intense, the GSD slightly larger and broader, "
     + COMPARISON_STYLE,
     "Belgian Malinois and German Shepherd side by side, elite "
     "working breeds compared"),
    ("chihuahua-vs-pomeranian",
     "A short-haired fawn Chihuahua on the left and a fluffy orange "
     "Pomeranian on the right, side by side on a clean studio backdrop, "
     "both facing the camera, the Chi visibly slimmer with large ears, "
     "the Pom fluffy and rounded with profuse coat, "
     + COMPARISON_STYLE,
     "Chihuahua and Pomeranian side by side studio portrait, two "
     "popular toy breeds compared"),
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
