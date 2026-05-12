"""Generate split-frame hero images for the 5 comparison articles via fal.ai.

Each hero shows both compared breeds side-by-side in a clean studio composition.

One-shot run: python3 scripts/generate_comparison_heroes.py
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import generate_breed_images as gbi
import shopify_files_upload as sfu

OUT_DIR = ROOT / "sample-images" / "comparison-heroes"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "both dogs are the dominant subjects with full bodies and all legs clearly visible, "
    "soft natural daylight, shallow depth of field with sharp focus on both dogs, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

PROMPTS: dict[str, tuple[str, str]] = {
    "goldendoodle-vs-labradoodle": (
        f"Two dogs side by side facing the camera on a clean studio cream-colored floor: "
        f"on the left, a cream-and-apricot wavy-coat Goldendoodle with a teddy-bear face; "
        f"on the right, a chocolate fleece-coat Labradoodle. Both sitting alert, similar size, "
        f"side-by-side comparison composition, even soft studio lighting, {STYLE_TAIL}",
        "Goldendoodle and Labradoodle side by side, head-to-head breed comparison",
    ),
    "labrador-retriever-vs-golden-retriever": (
        f"Two dogs side by side facing the camera on a sunlit grass meadow: on the left, "
        f"a yellow Labrador Retriever with short dense coat and otter tail; on the right, "
        f"a Golden Retriever with rich golden flowing long coat and feathering. Both sitting "
        f"alert, similar size, side-by-side comparison composition, warm afternoon light, {STYLE_TAIL}",
        "Labrador Retriever and Golden Retriever side by side, breed comparison",
    ),
    "bernedoodle-vs-goldendoodle": (
        f"Two dogs side by side on a clean studio cream-colored floor: on the left, a tri-color "
        f"(black with white markings and rust accents) wavy-coat Bernedoodle; on the right, a "
        f"cream-and-apricot wavy-coat Goldendoodle. Both sitting alert, side-by-side comparison "
        f"composition, even soft studio lighting, {STYLE_TAIL}",
        "Bernedoodle and Goldendoodle side by side, doodle breed comparison",
    ),
    "cavapoo-vs-cockapoo": (
        f"Two small dogs side by side on a soft cream rug: on the left, an apricot wavy-coat "
        f"Cavapoo with a rounded teddy-bear muzzle; on the right, a chocolate wavy-coat Cockapoo "
        f"with longer feathering on the ears. Both sitting alert, similar small size, side-by-side "
        f"comparison composition, warm soft window light, blurred warm interior background, {STYLE_TAIL}",
        "Cavapoo and Cockapoo side by side, small doodle breed comparison",
    ),
    "standard-poodle-vs-goldendoodle": (
        f"Two dogs side by side on a clean studio cream-colored floor: on the left, an elegant "
        f"apricot Standard Poodle in a refined sporting clip; on the right, a cream-and-apricot "
        f"wavy-coat Goldendoodle with teddy-bear face. Both sitting alert, similar size, side-by-side "
        f"comparison composition, even soft studio lighting, {STYLE_TAIL}",
        "Standard Poodle and Goldendoodle side by side, purebred vs doodle comparison",
    ),
}


def gen_and_upload(fal_key: str, store: str, token: str, slug: str, prompt: str, alt: str) -> tuple[str, str, str]:
    print(f"[{slug}] generating...", flush=True)
    src_path = gbi.run_one(fal_key, slug, prompt, OUT_DIR)
    unique = OUT_DIR / f"comparison-{slug}-hero.png"
    if src_path != unique:
        if unique.exists():
            unique.unlink()
        src_path.rename(unique)
    print(f"[{slug}] uploading...", flush=True)
    cdn_url = sfu.upload_one(store, token, unique, alt=alt)
    return slug, cdn_url, alt


def main() -> int:
    fal_key = gbi.load_fal_key()
    env = sfu.load_env()
    store = env.get("SHOPIFY_STORE", "")
    token = env.get("SHOPIFY_TOKEN", "")
    if not store or not token:
        sys.exit("missing SHOPIFY_STORE/TOKEN in .env")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(PROMPTS)} comparison hero images (~${len(PROMPTS) * 0.16:.2f})...")
    results: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(gen_and_upload, fal_key, store, token, s, p, a): s for s, (p, a) in PROMPTS.items()}
        for fut in as_completed(futures):
            s = futures[fut]
            try:
                slug, url, alt = fut.result()
                results[slug] = (url, alt)
            except Exception as e:
                print(f"  FAIL {s}: {e}", flush=True)

    print(f"\nPatching {len(results)} comparison JSONs...")
    for slug, (url, alt) in results.items():
        p = BREED_DATA / f"{slug}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        hero = d.setdefault("images", {}).setdefault("hero", {})
        old = hero.get("url", "")
        hero["url"] = url
        hero["alt"] = alt
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {slug}: {old[:50]}... -> {url[:70]}...")

    print(f"\nDone. {len(results)}/{len(PROMPTS)} succeeded")
    return 0 if len(results) == len(PROMPTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
