"""Generate split-frame hero images for the 5 v2 comparison articles via fal.ai.

One-shot run: python3 scripts/generate_comparison_heroes_v2.py
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

OUT_DIR = ROOT / "sample-images" / "comparison-heroes-v2"
BREED_DATA = ROOT / "breed-data"

STYLE_TAIL = (
    "both dogs are the dominant subjects with full bodies clearly visible, "
    "soft natural daylight, shallow depth of field with sharp focus on both dogs, "
    "professional pet photography, photorealistic, magazine cover quality, no humans, no text"
)

PROMPTS: dict[str, tuple[str, str]] = {
    "rottweiler-vs-cane-corso": (
        f"Two large mastiff-derived dogs standing side by side on a sunlit grass meadow: "
        f"on the left, a powerful Rottweiler with short black-and-tan coat and broad chest; "
        f"on the right, a taller athletic Cane Corso with short brindle coat and confident stance. "
        f"Both standing alert in three-quarter angle, similar pose, side-by-side comparison "
        f"composition, warm afternoon light, blurred grass and trees background, {STYLE_TAIL}",
        "Rottweiler and Cane Corso side by side, mastiff guardian breed comparison",
    ),
    "cane-corso-vs-presa-canario": (
        f"Two massive mastiff-type dogs standing side by side on a clean studio cream-colored "
        f"floor: on the left, a Cane Corso with brindle coat, athletic build, and refined head; "
        f"on the right, a Presa Canario with brindle coat plus distinctive black mask, heavier "
        f"build, and catlike rounded feet. Both standing alert in three-quarter angle, side-by-side "
        f"comparison composition, even soft studio lighting, {STYLE_TAIL}",
        "Cane Corso and Presa Canario side by side, Mediterranean mastiff comparison",
    ),
    "german-shepherd-vs-doberman": (
        f"Two working dogs standing side by side on a sunlit stone path: on the left, "
        f"a German Shepherd with classic black-and-tan double coat and slight slope to back; "
        f"on the right, a sleek Doberman Pinscher with black-and-rust short coat and elegant lean "
        f"build. Both standing alert in three-quarter angle, side-by-side comparison composition, "
        f"warm afternoon light, blurred suburban background, {STYLE_TAIL}",
        "German Shepherd and Doberman Pinscher side by side, working breed comparison",
    ),
    "rottweiler-vs-doberman-pinscher": (
        f"Two powerful guard breeds standing side by side on a sunlit grass meadow: on the "
        f"left, a Rottweiler with stocky build, broad chest, and black-and-tan coat; on the "
        f"right, a Doberman Pinscher with lean athletic build and black-and-rust sleek coat. "
        f"Both standing alert in three-quarter angle showing size and build contrast, side-by-side "
        f"comparison composition, warm afternoon light, blurred natural background, {STYLE_TAIL}",
        "Rottweiler and Doberman Pinscher side by side, guard breed comparison",
    ),
    "border-collie-vs-australian-shepherd": (
        f"Two herding dogs standing alert side by side on a sunlit grass meadow: on the left, "
        f"a Border Collie with classic black-and-white coat, lean build, intense focused gaze; "
        f"on the right, an Australian Shepherd with blue merle coat, slightly heavier build, "
        f"and characteristic blue eyes. Both standing alert in three-quarter angle, side-by-side "
        f"comparison composition, warm afternoon light, blurred pasture background, {STYLE_TAIL}",
        "Border Collie and Australian Shepherd side by side, herding breed comparison",
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

    print(f"Generating {len(PROMPTS)} v2 comparison hero images (~${len(PROMPTS) * 0.16:.2f})...")
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
